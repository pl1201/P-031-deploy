/**
 * Nhãn tiếng Việt dùng chung cho các mã enum lâm sàng — trước đây mỗi trang tự
 * copy 1 bản riêng (ít nhất 4 file), dẫn tới lệch nhãn giữa các trang (VD
 * "ĐTĐ type 2" ở trang danh sách bệnh nhân vs "Đái tháo đường type 2" ở nơi
 * khác cho cùng mã T2DM) và dễ quên áp dụng ở chỗ mới. Gộp về 1 nguồn duy nhất.
 */
export const CONDITION_LABELS: Record<string, string> = {
  T2DM: 'Đái tháo đường type 2', HTN: 'Tăng huyết áp', CKD: 'Bệnh thận mạn', GOUT: 'Gout',
}

export const ACTIVITY_LABELS: Record<string, string> = {
  light: 'Nhẹ', moderate: 'Trung bình', heavy: 'Nặng', very_heavy: 'Rất nặng',
}

/** Không có tiền tố "Miền" — ghép tại nơi dùng vì không phải chỗ nào cũng cần. */
export const REGION_LABELS: Record<string, string> = { north: 'Bắc', central: 'Trung', south: 'Nam' }
