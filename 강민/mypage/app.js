const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));
const API_BASE = "/api/mypage";

let state = {
  activeView: "home",
  selectedOrderId: null,
  summary: null,
  profile: null,
  orders: [],
  selectedOrder: null,
  payments: [],
  selectedPaymentId: null,
  selectedPayment: null,
  wishlist: [],
  recent: []
};

const formatPrice = (value) => `${Number(value).toLocaleString("ko-KR")} KRW`;

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      "X-Mock-User": "1",
      ...options.headers
    },
    ...options
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.message || "Request failed.");
  return payload;
}

const mypageApi = {
  getSummary: () => request("/summary"),
  getProfile: () => request("/profile"),
  updateProfile: (profile) => request("/profile", { method: "PATCH", body: JSON.stringify(profile) }),
  getOrders: () => request("/orders"),
  getOrderDetail: (orderId) => request(`/orders/${encodeURIComponent(orderId)}`),
  getPayments: () => request("/payments"),
  getPaymentDetail: (paymentId) => request(`/payments/${encodeURIComponent(paymentId)}`),
  getWishlist: () => request("/wishlist"),
  deleteWishlist: (productId) => request(`/wishlist/${encodeURIComponent(productId)}`, { method: "DELETE" }),
  getRecentProducts: () => request("/recent-products"),
  reset: () => request("/reset", { method: "POST" })
};

function setStatus(message = "", isError = false) {
  const status = $("#statusMessage");
  if (!status) return;
  status.textContent = message;
  status.classList.toggle("error", isError);
  status.classList.toggle("hidden", !message);
}

function setView(viewName) {
  state.activeView = viewName;
  $$(".rail-item").forEach((tab) => tab.classList.toggle("active", tab.dataset.view === viewName));
  $$(".view").forEach((view) => view.classList.toggle("active", view.id === `${viewName}View`));
}

function updateSummary() {
  const activeWishCount = state.summary?.wishlistCount ?? state.wishlist.filter((item) => item.active).length;
  const orderCount = state.summary?.orderCount ?? state.orders.length;
  const paymentCount = state.summary?.paymentCount ?? state.payments.length;
  const recentCount = state.summary?.recentProductCount ?? state.recent.length;
  const nextOrder = state.summary?.nextOrder;

  $("#avatarInitial").textContent = state.profile?.name?.trim().slice(0, 1) || "U";
  $("#heroName").textContent = state.profile?.name || "User";
  $("#heroEmail").textContent = state.profile?.email || "Login required";
  $("#orderCount").textContent = orderCount;
  $("#paymentCount").textContent = paymentCount;
  $("#wishCount").textContent = activeWishCount;
  $("#recentCount").textContent = recentCount;
  $("#orderNavCount").textContent = `${orderCount} orders`;
  $("#paymentNavCount").textContent = `${paymentCount} items`;
  $("#wishNavCount").textContent = `${activeWishCount} items`;
  $("#recentNavCount").textContent = `${recentCount} items`;
  $("#nextActionTitle").textContent = nextOrder ? `${nextOrder.status} order` : "No orders";
  $("#nextActionCopy").textContent = nextOrder
    ? `${nextOrder.orderId} has ${nextOrder.itemCount} item(s) to review.`
    : "Order status appears here after checkout.";
}

function renderProfile() {
  const form = $("#profileForm");
  if (!state.profile) return;
  form.elements.name.value = state.profile.name;
  form.elements.email.value = state.profile.email;
  form.elements.phone.value = state.profile.phone;
  form.elements.address.value = state.profile.address;
}

function setProfileEditMode(enabled) {
  const form = $("#profileForm");
  Array.from(form.elements).forEach((element) => {
    if (element.tagName === "INPUT") element.disabled = !enabled;
  });
  $("#profileActions").classList.toggle("hidden", !enabled);
  $$('[data-action="edit-profile"]').forEach((button) => button.classList.toggle("hidden", enabled));
  if (enabled) {
    setView("profile");
    form.elements.name.focus();
  }
}

function renderOrders() {
  const list = $("#orderList");
  if (!state.orders.length) {
    list.innerHTML = `<article class="empty-card">No orders yet.</article>`;
    $("#orderDetail").innerHTML = `<p>Select an order to view details.</p>`;
    return;
  }
  list.innerHTML = state.orders.map((order) => `
    <button class="order-card ${order.orderId === state.selectedOrderId ? "active" : ""}" type="button" data-order-id="${order.orderId}">
      <div class="order-head">
        <span>
          <span class="order-id">${order.orderId}</span>
          <strong class="order-title">${order.title}</strong>
        </span>
        <span class="order-status">${order.status}</span>
      </div>
      <div class="order-meta">
        <span>${order.orderedAt}</span>
        <span>${order.itemCount} item(s)</span>
        <span>${formatPrice(order.totalAmount)}</span>
      </div>
    </button>
  `).join("");
}

function renderOrderDetail() {
  const detail = $("#orderDetail");
  const order = state.selectedOrder;
  if (!order) {
    detail.innerHTML = `<p>Select an order to view details.</p>`;
    return;
  }
  detail.innerHTML = `
    <p class="eyebrow">ORDER DETAIL</p>
    <h3>${order.status}</h3>
    <p class="order-meta">${order.orderId} - ${order.orderedAt}</p>
    <ul>
      ${order.items.map((item) => `
        <li>
          <span>${item.productName} x ${item.quantity}</span>
          <strong>${formatPrice(item.price * item.quantity)}</strong>
        </li>
      `).join("")}
    </ul>
    <div class="detail-total">
      <span>Total</span>
      <strong>${formatPrice(order.totalAmount)}</strong>
    </div>
    <div class="detail-actions">
      ${(order.availableActions || []).map((action) => `
        <button class="${action === "cancel" ? "danger-button" : "text-button"}" type="button" data-order-action="${action}">
          ${action === "pay" ? "Go to payment" : "Request cancel"}
        </button>
      `).join("")}
    </div>
  `;
}

function renderPayments() {
  const list = $("#paymentList");
  if (!state.payments.length) {
    list.innerHTML = `<article class="empty-card">No payment history.</article>`;
    $("#paymentDetail").innerHTML = `<p>Select a payment to view details.</p>`;
    return;
  }
  list.innerHTML = state.payments.map((payment) => `
    <button class="order-card ${payment.paymentId === state.selectedPaymentId ? "active" : ""}" type="button" data-payment-id="${payment.paymentId}">
      <div class="order-head">
        <span>
          <span class="order-id">${payment.paymentId}</span>
          <strong class="order-title">${payment.method}</strong>
        </span>
        <span class="order-status">${payment.status}</span>
      </div>
      <div class="order-meta">
        <span>${payment.paidAt}</span>
        <span>${payment.orderId}</span>
        <span>${formatPrice(payment.amount)}</span>
      </div>
    </button>
  `).join("");
}

function renderPaymentDetail() {
  const detail = $("#paymentDetail");
  const payment = state.selectedPayment;
  if (!payment) {
    detail.innerHTML = `<p>Select a payment to view details.</p>`;
    return;
  }
  detail.innerHTML = `
    <p class="eyebrow">PAYMENT DETAIL</p>
    <h3>${payment.status}</h3>
    <ul>
      <li><span>Payment ID</span><strong>${payment.paymentId}</strong></li>
      <li><span>Order ID</span><strong>${payment.orderId}</strong></li>
      <li><span>Method</span><strong>${payment.method}</strong></li>
      <li><span>Paid at</span><strong>${payment.paidAt}</strong></li>
      <li><span>Approval no</span><strong>${payment.approvalNo}</strong></li>
    </ul>
    <div class="detail-total">
      <span>Amount</span>
      <strong>${formatPrice(payment.amount)}</strong>
    </div>
  `;
}

function productRow(item, options = {}) {
  const isWishlist = Boolean(options.wishlist);
  const disabled = isWishlist && !item.active;
  const buttonText = isWishlist ? (item.active ? "Remove" : "Restore") : "View";
  const buttonClass = isWishlist && item.active ? "danger-button" : "text-button";
  const metaText = item.viewedAt ? `${item.category} - ${item.viewedAt}` : item.category;
  return `
    <article class="product-row ${disabled ? "disabled" : ""}">
      <img class="product-image" src="${item.imageUrl}" alt="${item.productName}">
      <div class="product-body">
        <div class="product-head">
          <span>
            <span class="product-brand">${item.brand}</span>
            <strong class="product-title">${item.productName}</strong>
          </span>
        </div>
        <div class="product-meta"><span>${metaText}</span></div>
        <div class="product-actions">
          <strong class="price">${formatPrice(item.price)}</strong>
          <button class="${buttonClass}" type="button" ${isWishlist ? `data-wishlist-id="${item.productId}"` : ""}>${buttonText}</button>
        </div>
      </div>
    </article>
  `;
}

function renderWishlist() {
  $("#wishlistGrid").innerHTML = state.wishlist.length
    ? state.wishlist.map((item) => productRow(item, { wishlist: true })).join("")
    : `<article class="empty-card">No wishlist items.</article>`;
}

function renderRecent() {
  $("#recentGrid").innerHTML = state.recent.length
    ? state.recent.map((item) => productRow(item)).join("")
    : `<article class="empty-card">No recently viewed products.</article>`;
}

function renderAll() {
  updateSummary();
  renderProfile();
  renderOrders();
  renderOrderDetail();
  renderPayments();
  renderPaymentDetail();
  renderWishlist();
  renderRecent();
}

async function loadInitialData() {
  setStatus("Loading mock API data...");
  try {
    const [summary, profile, orders, payments, wishlist, recent] = await Promise.all([
      mypageApi.getSummary(),
      mypageApi.getProfile(),
      mypageApi.getOrders(),
      mypageApi.getPayments(),
      mypageApi.getWishlist(),
      mypageApi.getRecentProducts()
    ]);
    state.summary = summary;
    state.profile = profile;
    state.orders = orders;
    state.payments = payments;
    state.wishlist = wishlist;
    state.recent = recent;
    state.selectedOrderId = orders[0]?.orderId ?? null;
    state.selectedOrder = state.selectedOrderId ? await mypageApi.getOrderDetail(state.selectedOrderId) : null;
    state.selectedPaymentId = payments[0]?.paymentId ?? null;
    state.selectedPayment = state.selectedPaymentId ? await mypageApi.getPaymentDetail(state.selectedPaymentId) : null;
    renderAll();
    setView(state.activeView);
    setStatus("");
  } catch (error) {
    setStatus(error.message, true);
  }
}

document.addEventListener("click", async (event) => {
  const viewTrigger = event.target.closest("[data-view]");
  if (viewTrigger) {
    setView(viewTrigger.dataset.view);
    return;
  }
  const orderRow = event.target.closest("[data-order-id]");
  if (orderRow) {
    try {
      state.selectedOrderId = orderRow.dataset.orderId;
      state.selectedOrder = await mypageApi.getOrderDetail(state.selectedOrderId);
      renderOrders();
      renderOrderDetail();
    } catch (error) {
      setStatus(error.message, true);
    }
    return;
  }
  const wishlistButton = event.target.closest("[data-wishlist-id]");
  if (wishlistButton) {
    try {
      await mypageApi.deleteWishlist(wishlistButton.dataset.wishlistId);
      const [summary, wishlist] = await Promise.all([mypageApi.getSummary(), mypageApi.getWishlist()]);
      state.summary = summary;
      state.wishlist = wishlist;
      updateSummary();
      renderWishlist();
      setStatus("Wishlist updated.");
      setTimeout(() => setStatus(""), 1600);
    } catch (error) {
      setStatus(error.message, true);
    }
    return;
  }
  const paymentRow = event.target.closest("[data-payment-id]");
  if (paymentRow) {
    try {
      state.selectedPaymentId = paymentRow.dataset.paymentId;
      state.selectedPayment = await mypageApi.getPaymentDetail(state.selectedPaymentId);
      renderPayments();
      renderPaymentDetail();
    } catch (error) {
      setStatus(error.message, true);
    }
    return;
  }
  const orderAction = event.target.closest("[data-order-action]");
  if (orderAction) {
    const actionText = orderAction.dataset.orderAction === "pay"
      ? "Payment flow will be handled by the payment domain."
      : "Cancel flow will be handled by the order/payment domain.";
    setStatus(actionText);
    setTimeout(() => setStatus(""), 2200);
    return;
  }
  const actionButton = event.target.closest("[data-action]");
  if (!actionButton) return;
  if (actionButton.dataset.action === "edit-profile") setProfileEditMode(true);
  if (actionButton.dataset.action === "cancel-profile") {
    renderProfile();
    setProfileEditMode(false);
  }
  if (actionButton.dataset.action === "refresh") {
    try {
      await mypageApi.reset();
      state.activeView = "home";
      setProfileEditMode(false);
      await loadInitialData();
    } catch (error) {
      setStatus(error.message, true);
    }
  }
});

document.addEventListener("keydown", (event) => {
  const card = event.target.closest(".stat-card");
  if (!card || (event.key !== "Enter" && event.key !== " ")) return;
  event.preventDefault();
  setView(card.dataset.view);
});

$("#profileForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    state.profile = await mypageApi.updateProfile({
      name: form.elements.name.value.trim(),
      email: form.elements.email.value.trim(),
      phone: form.elements.phone.value.trim(),
      address: form.elements.address.value.trim()
    });
    state.summary = await mypageApi.getSummary();
    setProfileEditMode(false);
    renderAll();
    setStatus("Profile updated.");
    setTimeout(() => setStatus(""), 1600);
  } catch (error) {
    setStatus(error.message, true);
  }
});

loadInitialData();
