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

const formatPrice = (value) => `${Number(value).toLocaleString("ko-KR")}원`;

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
  if (!response.ok) throw new Error(payload.message || "요청 처리 중 오류가 발생했습니다.");
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
  $("#heroName").textContent = state.profile?.name || "사용자";
  $("#heroEmail").textContent = state.profile?.email || "로그인이 필요합니다";
  $("#orderCount").textContent = orderCount;
  $("#paymentCount").textContent = paymentCount;
  $("#wishCount").textContent = activeWishCount;
  $("#recentCount").textContent = recentCount;
  $("#orderNavCount").textContent = `${orderCount}건`;
  $("#paymentNavCount").textContent = `${paymentCount}건`;
  $("#wishNavCount").textContent = `${activeWishCount}개`;
  $("#recentNavCount").textContent = `${recentCount}개`;
  $("#nextActionTitle").textContent = nextOrder ? `${nextOrder.status} 주문 확인` : "주문 내역 없음";
  $("#nextActionCopy").textContent = nextOrder
    ? `${nextOrder.orderId} 주문의 상품 ${nextOrder.itemCount}개를 확인할 수 있습니다.`
    : "첫 주문을 완료하면 이 영역에서 상태를 확인할 수 있습니다.";
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
    list.innerHTML = `<article class="empty-card">주문 내역이 없습니다.</article>`;
    $("#orderDetail").innerHTML = `<p>주문을 선택하면 상세 정보가 표시됩니다.</p>`;
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
        <span>${order.itemCount}개 상품</span>
        <span>${formatPrice(order.totalAmount)}</span>
      </div>
    </button>
  `).join("");
}

function renderOrderDetail() {
  const detail = $("#orderDetail");
  const order = state.selectedOrder;
  if (!order) {
    detail.innerHTML = `<p>주문을 선택하면 상세 정보가 표시됩니다.</p>`;
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
      <span>총 결제금액</span>
      <strong>${formatPrice(order.totalAmount)}</strong>
    </div>
    <div class="detail-actions">
      ${(order.availableActions || []).map((action) => `
        <button class="${action === "cancel" ? "danger-button" : "text-button"}" type="button" data-order-action="${action}">
          ${action === "pay" ? "결제하기" : "취소 요청"}
        </button>
      `).join("")}
    </div>
  `;
}

function renderPayments() {
  const list = $("#paymentList");
  if (!state.payments.length) {
    list.innerHTML = `<article class="empty-card">결제 내역이 없습니다.</article>`;
    $("#paymentDetail").innerHTML = `<p>결제를 선택하면 상세 정보가 표시됩니다.</p>`;
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
    detail.innerHTML = `<p>결제를 선택하면 상세 정보가 표시됩니다.</p>`;
    return;
  }
  detail.innerHTML = `
    <p class="eyebrow">PAYMENT DETAIL</p>
    <h3>${payment.status}</h3>
    <ul>
      <li><span>결제 ID</span><strong>${payment.paymentId}</strong></li>
      <li><span>주문번호</span><strong>${payment.orderId}</strong></li>
      <li><span>결제수단</span><strong>${payment.method}</strong></li>
      <li><span>결제일시</span><strong>${payment.paidAt}</strong></li>
      <li><span>승인번호</span><strong>${payment.approvalNo}</strong></li>
    </ul>
    <div class="detail-total">
      <span>결제금액</span>
      <strong>${formatPrice(payment.amount)}</strong>
    </div>
  `;
}

function productRow(item, options = {}) {
  const isWishlist = Boolean(options.wishlist);
  const disabled = isWishlist && !item.active;
  const buttonText = isWishlist ? (item.active ? "찜 해제" : "찜 복구") : "상품 보기";
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
    : `<article class="empty-card">찜한 상품이 없습니다.</article>`;
}

function renderRecent() {
  $("#recentGrid").innerHTML = state.recent.length
    ? state.recent.map((item) => productRow(item)).join("")
    : `<article class="empty-card">최근 본 상품이 없습니다.</article>`;
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
  setStatus("목업 API 데이터를 불러오는 중입니다.");
  try {
    const [summary, profile, orders, wishlist, recent] = await Promise.all([
      mypageApi.getSummary(),
      mypageApi.getProfile(),
      mypageApi.getOrders(),
      mypageApi.getWishlist(),
      mypageApi.getRecentProducts()
    ]);

    state.summary = summary;
    state.profile = profile;
    state.orders = orders;
    state.wishlist = wishlist;
    state.recent = recent;
    state.selectedOrderId = orders[0]?.orderId ?? null;
    state.selectedOrder = state.selectedOrderId ? await mypageApi.getOrderDetail(state.selectedOrderId) : null;

    try {
      state.payments = await mypageApi.getPayments();
      state.selectedPaymentId = state.payments[0]?.paymentId ?? null;
      state.selectedPayment = state.selectedPaymentId ? await mypageApi.getPaymentDetail(state.selectedPaymentId) : null;
    } catch (error) {
      state.payments = [];
      state.selectedPaymentId = null;
      state.selectedPayment = null;
      setStatus("결제 API가 없는 이전 목업 서버입니다. 서버를 재시작하면 결제 내역이 표시됩니다.", true);
    }

    renderAll();
    setView(state.activeView);
    if (state.payments.length) setStatus("");
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
      setStatus("찜 상태가 변경되었습니다.");
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
      ? "결제 처리는 결제 도메인에서 담당합니다."
      : "주문/결제 취소 처리는 주문·결제 도메인에서 담당합니다.";
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
    setStatus("내 정보가 수정되었습니다.");
    setTimeout(() => setStatus(""), 1600);
  } catch (error) {
    setStatus(error.message, true);
  }
});

loadInitialData();
