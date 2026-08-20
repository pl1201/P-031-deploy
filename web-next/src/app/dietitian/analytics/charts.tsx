'use client'

import { Cell, Pie, PieChart, ResponsiveContainer } from 'recharts'

// Các chart trong file này CHỈ trực quan hoá lại số đã tính sẵn trong buildModel()
// (page.tsx) — không tự tính lại hay suy đoán thêm giá trị dinh dưỡng/lâm sàng
// nào (RULE-1/RULE-2). Dùng Tailwind + recharts riêng cho trang analytics theo
// yêu cầu thiết kế; phần còn lại của web-next vẫn là CSS Modules thuần
// (xem tailwind-scope.css — không đổi quy ước toàn app).

export type DonutSlice = { key: string; label: string; value: number; color: string }

function DonutCenter({ value, caption }: { value: string; caption: string }) {
  return (
    <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
      <span className="text-3xl font-bold leading-none text-slate-800 dark:text-slate-100">{value}</span>
      <span className="mt-1 text-[11px] font-medium text-gray-500 dark:text-slate-400">{caption}</span>
    </div>
  )
}

function DonutLegend({ slices }: { slices: DonutSlice[] }) {
  return (
    <ul className="flex min-w-[150px] flex-1 flex-col gap-3">
      {slices.map(slice => (
        <li key={slice.key} className="flex items-center justify-between gap-3">
          <span className="flex items-center gap-2 text-[12.5px] font-medium text-slate-600 dark:text-slate-300">
            <span className="h-3 w-3 flex-none rounded-full" style={{ background: slice.color }} />
            {slice.label}
          </span>
          <strong className="font-mono text-[13px] font-bold text-slate-800 dark:text-slate-100">{slice.value}</strong>
        </li>
      ))}
    </ul>
  )
}

/** Donut dùng chung cho Block 03/04 — Pie/Cell của recharts + overlay số ở tâm tự dựng
 * (không dùng label mặc định của recharts) + legend HTML/Tailwind tự dựng bên phải.
 * `data` truyền vào <Pie> luôn giữ NGUYÊN CÙNG 1 mảng `slices` (không đổi shape/số
 * phần tử giữa "chưa có dữ liệu" và "có dữ liệu") — đổi shape giữa 2 lần render từng
 * làm recharts v3 nội suy animation sai, chỉ vẽ đúng 1 lát cắt đầy gần tròn thay vì
 * tỉ lệ thật. Trạng thái rỗng xử lý bằng vòng xám tĩnh riêng, không đụng tới <Pie>. */
function Donut({ slices, centerValue, centerCaption }: { slices: DonutSlice[]; centerValue: string; centerCaption: string }) {
  const total = slices.reduce((sum, slice) => sum + slice.value, 0)
  return (
    <div className="flex flex-col items-center gap-6 sm:flex-row">
      <div className="relative h-44 w-44 flex-none">
        {total > 0 ? (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={slices} dataKey="value" nameKey="label" innerRadius={60} outerRadius={80} stroke="none" paddingAngle={2} isAnimationActive={false}>
                {slices.map(slice => <Cell key={slice.key} fill={slice.color} />)}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full w-full rounded-full border-[20px] border-slate-200 dark:border-slate-700" />
        )}
        <DonutCenter value={centerValue} caption={centerCaption} />
      </div>
      <DonutLegend slices={slices} />
    </div>
  )
}

export function RiskDonut({ slices, total }: { slices: DonutSlice[]; total: number }) {
  return <Donut slices={slices} centerValue={String(total)} centerCaption="có đánh giá" />
}

export function ReadinessDonut({ ready, pending, percent }: { ready: number; pending: number; percent: number }) {
  const slices: DonutSlice[] = [
    { key: 'ready', label: 'Không có dòng chờ', value: ready, color: '#34D399' },
    { key: 'pending', label: 'Cần đối chiếu', value: pending, color: '#FBBF24' },
  ]
  return <Donut slices={slices} centerValue={`${percent}%`} centerCaption="sẵn sàng" />
}

export type FlowMetric = { key: string; label: string; count: number; percent: number; color: string }

/** Block 02 — thanh ngang bằng div/Tailwind thuần, KHÔNG dùng recharts (BarChart
 * layout="vertical" là over-engineered cho 4 thanh đơn giản này). */
export function DecisionFlow({ metrics }: { metrics: FlowMetric[] }) {
  return (
    <div className="grid grid-cols-2 gap-x-8 gap-y-6 sm:grid-cols-4">
      {metrics.map(metric => (
        <div key={metric.key} className="flex flex-col gap-2">
          <div className="flex items-baseline justify-between gap-2">
            <span className="text-[10.5px] font-bold uppercase tracking-wide text-slate-500 dark:text-slate-400">{metric.label}</span>
            <span className="font-mono text-[15px] font-bold text-slate-800 dark:text-slate-100">{metric.count}</span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-gray-200 dark:bg-slate-700">
            <div className="h-full rounded-full transition-[width] duration-500 ease-out" style={{ width: `${Math.max(metric.count ? 3 : 0, metric.percent)}%`, background: metric.color }} />
          </div>
          <span className="text-[10px] font-medium text-slate-400 dark:text-slate-500">{metric.percent}% tổng phương án</span>
        </div>
      ))}
    </div>
  )
}
