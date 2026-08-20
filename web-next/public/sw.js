// Service worker tối giản chỉ để thoả điều kiện "installable" (Add to Home Screen) của
// Chrome/Android — KHÔNG cache bất kỳ response nào. Dữ liệu lâm sàng (thực đơn, trạng thái
// duyệt) luôn phải lấy tươi từ server; cache cũ có thể khiến bệnh nhân/chuyên gia thấy sai
// trạng thái. Mọi request đều đi thẳng ra mạng, không có cache layer nào ở đây.
self.addEventListener('install', () => {
  self.skipWaiting()
})

self.addEventListener('activate', (event) => {
  event.waitUntil(self.clients.claim())
})

self.addEventListener('fetch', (event) => {
  // Chỉ can thiệp request GET — POST/PUT/DELETE (duyệt thực đơn, ghi nhật ký...)
  // để trình duyệt tự xử lý bình thường, SW không cần chen vào.
  if (event.request.method !== 'GET') return
  // .catch() bắt buộc: request bị huỷ giữa chừng (chuyển trang, HMR dev) khiến
  // fetch() reject — không bắt sẽ in "Uncaught (in promise) TypeError: Failed
  // to fetch" ra console dù không phải lỗi thật của app.
  event.respondWith(fetch(event.request).catch(() => new Response(null, { status: 503, statusText: 'Network error' })))
})
