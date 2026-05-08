const http = require("http");
const fs = require("fs");
const path = require("path");
const { URL } = require("url");

const PORT = Number(process.env.PORT || 5174);
const ROOT = path.join(__dirname, "\uac15\ubbfc", "mypage");

const initialData = {
  profile: {
    id: 1,
    name: "Kang Min",
    email: "kkm@example.com",
    phone: "010-1234-5678",
    address: "Hallym University, Chuncheon"
  },
  orders: [
    {
      orderId: "ORD-20260505-001",
      orderedAt: "2026-05-05",
      status: "Preparing shipment",
      totalAmount: 128000,
      items: [
        { productId: "P-1001", productName: "Oversized Check Shirt", quantity: 1, price: 48900 },
        { productId: "P-1002", productName: "Wide Denim Pants", quantity: 1, price: 79100 }
      ]
    },
    {
      orderId: "ORD-20260429-014",
      orderedAt: "2026-04-29",
      status: "Delivered",
      totalAmount: 73500,
      items: [
        { productId: "P-1003", productName: "Minimal Round Cardigan", quantity: 1, price: 37950 },
        { productId: "P-1004", productName: "Basic Logo T-Shirt", quantity: 1, price: 35550 }
      ]
    },
    {
      orderId: "ORD-20260418-006",
      orderedAt: "2026-04-18",
      status: "Confirmed",
      totalAmount: 39000,
      items: [
        { productId: "P-1005", productName: "Cargo Jogger Pants", quantity: 1, price: 39000 }
      ]
    }
  ],
  payments: [
    {
      paymentId: "PAY-20260505-001",
      orderId: "ORD-20260505-001",
      paidAt: "2026-05-05 14:28",
      status: "READY",
      method: "Toss Payments",
      amount: 128000,
      approvalNo: "-"
    },
    {
      paymentId: "PAY-20260429-014",
      orderId: "ORD-20260429-014",
      paidAt: "2026-04-29 19:03",
      status: "DONE",
      method: "Toss Payments",
      amount: 73500,
      approvalNo: "APRV-240429-014"
    },
    {
      paymentId: "PAY-20260418-006",
      orderId: "ORD-20260418-006",
      paidAt: "2026-04-18 11:42",
      status: "DONE",
      method: "Card",
      amount: 39000,
      approvalNo: "APRV-240418-006"
    }
  ],
  wishlist: [
    {
      productId: "3528683",
      brand: "NOT4NERD",
      productName: "Parachute Nylon Cargo Pants - Black",
      price: 43700,
      category: "Pants",
      active: true,
      imageUrl: "https://image.msscdn.net/images/goods_img/20230905/3528683/3528683_16970733118457_500.jpg"
    },
    {
      productId: "4336624",
      brand: "EXCONTAINER",
      productName: "Minimal Button Round Crop Cardigan",
      price: 37950,
      category: "Outer",
      active: true,
      imageUrl: "https://image.msscdn.net/images/goods_img/20240816/4336624/4336624_17706226040291_500.jpg"
    },
    {
      productId: "4306872",
      brand: "CGP",
      productName: "90S VTG Oversized Check Shirt",
      price: 31850,
      category: "Top",
      active: true,
      imageUrl: "https://image.msscdn.net/images/goods_img/20240807/4306872/4306872_17718107079304_500.jpg"
    }
  ],
  recent: [
    {
      productId: "4936037",
      brand: "VERDNT",
      productName: "Front Cargo Nylon Wide Pants",
      price: 38600,
      category: "Pants",
      viewedAt: "Today 21:18",
      imageUrl: "https://image.msscdn.net/images/goods_img/20250324/4936037/4936037_17688016226604_500.jpg"
    },
    {
      productId: "4375056",
      brand: "LMC",
      productName: "OVERDYED CITIZEN STANDARD HOODIE",
      price: 76300,
      category: "Top",
      viewedAt: "Yesterday 18:42",
      imageUrl: "https://image.msscdn.net/images/goods_img/20240827/4375056/4375056_17247390508394_500.jpg"
    },
    {
      productId: "5378824",
      brand: "EMIS",
      productName: "WIDE LOGO HAIRBAND",
      price: 39000,
      category: "Accessory",
      viewedAt: "05.04 12:03",
      imageUrl: "https://image.msscdn.net/images/goods_img/20250829/5378824/5378824_17564442945712_500.jpg"
    }
  ]
};

let db = clone(initialData);

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function sendJson(res, status, data) {
  res.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Cache-Control": "no-store"
  });
  res.end(JSON.stringify(data));
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let body = "";
    req.on("data", (chunk) => {
      body += chunk;
      if (body.length > 1_000_000) reject(new Error("Request body is too large."));
    });
    req.on("end", () => {
      try {
        resolve(body ? JSON.parse(body) : {});
      } catch {
        reject(new Error("Invalid JSON body."));
      }
    });
  });
}

function requireAuth(req, res) {
  if (req.headers["x-mock-user"] !== "1") {
    sendJson(res, 401, { message: "Login is required." });
    return false;
  }
  return true;
}

function orderSummary(order) {
  return {
    orderId: order.orderId,
    orderedAt: order.orderedAt,
    status: order.status,
    totalAmount: order.totalAmount,
    itemCount: order.items.length,
    title: `${order.items[0].productName}${order.items.length > 1 ? ` + ${order.items.length - 1} more` : ""}`
  };
}

function orderActions(order) {
  if (order.status === "Preparing shipment") return ["cancel"];
  if (order.status === "Pending payment") return ["pay", "cancel"];
  return [];
}

function paymentSummary(payment) {
  return {
    paymentId: payment.paymentId,
    orderId: payment.orderId,
    paidAt: payment.paidAt,
    status: payment.status,
    method: payment.method,
    amount: payment.amount
  };
}

async function handleApi(req, res, pathname) {
  if (!requireAuth(req, res)) return;

  if (req.method === "GET" && pathname === "/api/mypage/summary") {
    const activeWishlist = db.wishlist.filter((item) => item.active);
    const nextOrder = db.orders.find((order) => order.status !== "Confirmed");
    sendJson(res, 200, {
      profile: db.profile,
      orderCount: db.orders.length,
      paymentCount: db.payments.length,
      wishlistCount: activeWishlist.length,
      recentProductCount: db.recent.length,
      nextOrder: nextOrder ? {
        orderId: nextOrder.orderId,
        status: nextOrder.status,
        itemCount: nextOrder.items.length
      } : null
    });
    return;
  }

  if (req.method === "GET" && pathname === "/api/mypage/profile") {
    sendJson(res, 200, db.profile);
    return;
  }

  if (req.method === "PATCH" && pathname === "/api/mypage/profile") {
    const body = await readBody(req);
    const required = ["name", "email", "phone", "address"];
    const hasInvalid = required.some((key) => typeof body[key] !== "string" || !body[key].trim());
    if (hasInvalid) {
      sendJson(res, 400, { message: "Name, email, phone, and address are required." });
      return;
    }
    db.profile = {
      ...db.profile,
      name: body.name.trim(),
      email: body.email.trim(),
      phone: body.phone.trim(),
      address: body.address.trim()
    };
    sendJson(res, 200, db.profile);
    return;
  }

  if (req.method === "GET" && pathname === "/api/mypage/orders") {
    sendJson(res, 200, db.orders.map(orderSummary));
    return;
  }

  const orderMatch = pathname.match(/^\/api\/mypage\/orders\/([^/]+)$/);
  if (req.method === "GET" && orderMatch) {
    const orderId = decodeURIComponent(orderMatch[1]);
    const order = db.orders.find((item) => item.orderId === orderId);
    if (!order) {
      sendJson(res, 404, { message: "Order not found." });
      return;
    }
    sendJson(res, 200, { ...order, availableActions: orderActions(order) });
    return;
  }

  if (req.method === "GET" && pathname === "/api/mypage/payments") {
    sendJson(res, 200, db.payments.map(paymentSummary));
    return;
  }

  const paymentMatch = pathname.match(/^\/api\/mypage\/payments\/([^/]+)$/);
  if (req.method === "GET" && paymentMatch) {
    const paymentId = decodeURIComponent(paymentMatch[1]);
    const payment = db.payments.find((item) => item.paymentId === paymentId);
    if (!payment) {
      sendJson(res, 404, { message: "Payment not found." });
      return;
    }
    sendJson(res, 200, payment);
    return;
  }

  if (req.method === "GET" && pathname === "/api/mypage/wishlist") {
    sendJson(res, 200, db.wishlist);
    return;
  }

  const wishlistMatch = pathname.match(/^\/api\/mypage\/wishlist\/([^/]+)$/);
  if (req.method === "DELETE" && wishlistMatch) {
    const productId = decodeURIComponent(wishlistMatch[1]);
    const item = db.wishlist.find((product) => product.productId === productId);
    if (!item) {
      sendJson(res, 404, { message: "Wishlist item not found." });
      return;
    }
    item.active = !item.active;
    sendJson(res, 200, { productId, active: item.active });
    return;
  }

  if (req.method === "GET" && pathname === "/api/mypage/recent-products") {
    sendJson(res, 200, db.recent);
    return;
  }

  if (req.method === "POST" && pathname === "/api/mypage/reset") {
    db = clone(initialData);
    sendJson(res, 200, { ok: true });
    return;
  }

  sendJson(res, 404, { message: "Unsupported mock API." });
}

function serveStatic(req, res, pathname) {
  const target = pathname === "/" ? "/index.html" : pathname;
  const filePath = path.normalize(path.join(ROOT, target));
  if (!filePath.startsWith(ROOT)) {
    res.writeHead(403);
    res.end("Forbidden");
    return;
  }
  fs.readFile(filePath, (error, content) => {
    if (error) {
      res.writeHead(404);
      res.end("Not found");
      return;
    }
    const ext = path.extname(filePath).toLowerCase();
    const contentType = {
      ".html": "text/html; charset=utf-8",
      ".css": "text/css; charset=utf-8",
      ".js": "application/javascript; charset=utf-8",
      ".md": "text/plain; charset=utf-8"
    }[ext] || "application/octet-stream";
    res.writeHead(200, { "Content-Type": contentType });
    res.end(content);
  });
}

const server = http.createServer(async (req, res) => {
  const { pathname } = new URL(req.url, `http://${req.headers.host}`);
  try {
    if (pathname.startsWith("/api/")) {
      await handleApi(req, res, pathname);
      return;
    }
    serveStatic(req, res, pathname);
  } catch (error) {
    sendJson(res, 500, { message: error.message || "Mock server error." });
  }
});

server.on("error", (error) => {
  console.error(`Mock server failed: ${error.message}`);
  process.exitCode = 1;
});

server.listen(PORT, () => {
  console.log(`Mypage mock server running at http://localhost:${PORT}`);
});
