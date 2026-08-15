'use client'

import { FormEvent, createContext, useContext, useEffect, useRef, useState } from 'react'
import { usePathname } from 'next/navigation'
import { Icon } from '@/components/brand-artwork'
import styles from './experience-tools.module.css'
import v2 from './experience-tools-v2.module.css'

type Theme='light'|'dark'
type Message={id:number;from:'assistant'|'user';text:string}
type Reply={text:string;suggestions:string[]}

const STARTERS=['Tôi có thể hỏi gì?','Cách dùng bản demo','Hướng dẫn theo màn hình này','Thực đơn được kiểm tra thế nào?']
const DEFAULT_SUGGESTIONS=['Dành cho người bệnh','Dành cho chuyên gia','Mã hồ sơ là gì?','An toàn dữ liệu ra sao?']
const TOPICS=[
  {icon:'user',title:'Người bệnh',text:'Thực đơn, nhật ký và hồ sơ',question:'Dành cho người bệnh'},
  {icon:'expert',title:'Chuyên gia',text:'Tạo, kiểm tra và phê duyệt',question:'Dành cho chuyên gia'},
  {icon:'shield',title:'An toàn',text:'Nguồn dữ liệu và cảnh báo',question:'Kiểm tra an toàn gồm gì?'},
  {icon:'sparkles',title:'Theo màn hình',text:'Chỉ dẫn đúng nơi bạn đang xem',question:'Hướng dẫn theo màn hình này'},
]

function normalize(value:string){return value.toLocaleLowerCase('vi-VN').normalize('NFD').replace(/\p{Diacritic}/gu,'').replace(/đ/g,'d').replace(/[^a-z0-9\s]/g,' ').replace(/\s+/g,' ').trim()}

const KNOWLEDGE:Array<{keys:RegExp;answer:string;suggestions:string[]}>= [
  {keys:/(toi co the hoi gi|tro ly lam duoc gi|chuc nang|giup gi)/,answer:'Bạn có thể hỏi mình về cách dùng từng màn hình, đăng nhập demo, hồ sơ, tạo hoặc duyệt thực đơn, nhật ký món ăn, tổng hợp tuần, đối chiếu dữ liệu, mã hồ sơ, chế độ sáng/tối và cách xử lý lỗi thường gặp. Mình cũng giải thích ý nghĩa quy trình kiểm tra an toàn, nhưng không chẩn đoán hay kê đơn.',suggestions:['Hướng dẫn theo màn hình này','Quy trình thực đơn','Xử lý lỗi đăng nhập']},
  {keys:/(demo|dang nhap|tai khoan|mat khau|quen mat khau|trai nghiem)/,answer:'Tại trang đăng nhập, chọn Demo người bệnh để xem thực đơn, nhật ký và tuần của bạn; chọn Demo chuyên gia để quản lý hồ sơ, tạo phương án và duyệt. Nếu đăng nhập thường không thành công, hãy kiểm tra đúng vai trò, kết nối máy chủ và thử tải lại trang. Không chia sẻ mật khẩu trong khung chat.',suggestions:['Demo người bệnh có gì?','Demo chuyên gia có gì?','Không đăng nhập được']},
  {keys:/(nguoi benh|benh nhan|hom nay|mon da an)/,answer:'Không gian người bệnh gồm 4 khu vực: Hôm nay để xem thực đơn đã phát hành; Món đã ăn để ghi nhận thực tế; Tuần của tôi để xem mức độ đầy đủ dữ liệu; Hồ sơ để kiểm tra thông tin đang được dùng. Người bệnh không nhìn thấy bản nháp chưa được chuyên gia duyệt.',suggestions:['Cách ghi món đã ăn','Vì sao chưa có thực đơn?','Cập nhật hồ sơ']},
  {keys:/(chuyen gia|dinh duong vien|hang cho|quyet dinh)/,answer:'Không gian chuyên gia ưu tiên ca cần quyết định. Bạn có thể tìm hồ sơ, tạo phương án, xem bằng chứng kiểm tra, duyệt hoặc từ chối, đối chiếu món chưa rõ và xử lý yêu cầu cập nhật. Mỗi quyết định được gắn với đúng phiên bản thực đơn để có thể truy vết.',suggestions:['Cách tạo thực đơn','Cách duyệt thực đơn','Đối chiếu nhật ký']},
  {keys:/(tao thuc don|tao phuong an|lap ke hoach)/,answer:'Để tạo thực đơn: chọn đúng hồ sơ, kiểm tra thuốc/dị ứng và mục tiêu, đặt ngày áp dụng cùng cấu trúc bữa, rồi chọn Tạo phương án. Backend sẽ tính dinh dưỡng và chạy các kiểm tra. Sau đó chuyên gia cần đọc bằng chứng trước khi duyệt; giao diện không tự phát hành bản nháp.',suggestions:['Kiểm tra an toàn gồm gì?','Vì sao nút tạo bị khóa?','Cách duyệt sau khi tạo']},
  {keys:/(duyet|tu choi|phe duyet|phat hanh)/,answer:'Ở hàng chờ duyệt, mở từng bản để xem tóm tắt dinh dưỡng, cảnh báo, nguồn dữ liệu và phiên bản. Chỉ duyệt khi không còn chặn an toàn và dữ liệu đủ để quyết định. Khi từ chối, ghi lý do cụ thể. Chỉ bản đã duyệt mới được phát hành sang không gian người bệnh.',suggestions:['Cảnh báo P0/P1 là gì?','Duyệt nhiều bản','Người bệnh thấy gì?']},
  {keys:/(kiem tra|an toan|p0|p1|canh bao|di ung|thuoc)/,answer:'Hệ thống đối chiếu năng lượng, carbohydrate, phân bổ bữa, GI/GL, dị ứng, thuốc và các ràng buộc có nguồn. Cảnh báo nghiêm trọng hoặc dữ liệu thiếu có thể chặn phê duyệt. Đây là lớp hỗ trợ quyết định: chuyên gia vẫn phải đọc bằng chứng và chịu trách nhiệm phê duyệt.',suggestions:['Nguồn dữ liệu ở đâu?','Thuốc được đối chiếu thế nào?','Có tự động duyệt không?']},
  {keys:/(nhat ky|ghi mon|mon da an|khau phan|gram)/,answer:'Trong Món đã ăn, nhập tên món quen thuộc, khẩu phần nếu biết và bữa ăn tương ứng. Nếu không nhớ chính xác gram, bạn có thể để trống; hệ thống sẽ không tự bịa số liệu. Món chưa khớp được đưa vào hàng chờ để chuyên gia đối chiếu.',suggestions:['Món chưa đối chiếu là gì?','Xem tổng hợp tuần','Báo bỏ bữa']},
  {keys:/(tuan cua toi|tong hop tuan|bao cao tuan)/,answer:'Trang Tuần của tôi tổng hợp số ngày có ghi nhận, bữa đã ghi, bữa bỏ và món chờ đối chiếu. Khi dữ liệu chưa đủ, hệ thống hiển thị rõ “chưa tính được” thay vì kết luận đạt hay không đạt. Mục tiêu là nhận biết xu hướng, không phán xét một bữa riêng lẻ.',suggestions:['Bao nhiêu ngày là đủ?','Món chờ đối chiếu','Ghi bữa hôm nay']},
  {keys:/(doi chieu|mon chua ro|khong du du lieu)/,answer:'Đối chiếu nhật ký chỉ hiển thị món chưa rõ hoặc bữa cần chú ý. Chuyên gia chọn món phù hợp và khẩu phần để tính lại, hoặc đánh dấu Không đủ dữ liệu. Hệ thống không tự đoán món khi độ chắc chắn thấp.',suggestions:['Cách chọn món phù hợp','Vì sao không tự đoán?','Quay lại hàng chờ']},
  {keys:/(ho so|cap nhat thong tin|chieu cao|can nang|benh ly)/,answer:'Hồ sơ chứa dữ liệu dùng để cá nhân hóa và kiểm tra an toàn như tuổi, giới tính, chiều cao, cân nặng, bệnh lý, thuốc, dị ứng và khẩu vị. Người bệnh có thể gửi yêu cầu cập nhật; thay đổi lâm sàng cần chuyên gia xác nhận trước khi áp dụng.',suggestions:['Mã hồ sơ là gì?','Gửi yêu cầu cập nhật','Ai được sửa hồ sơ?']},
  {keys:/(ma ho so|ma benh nhan|id|dau thang)/,answer:'Chuỗi hiển thị sau “ID:” hoặc “Mã hồ sơ” là mã định danh hồ sơ trong hệ thống, không phải số căn cước hay mã bảo hiểm. Mã này giúp tìm đúng hồ sơ và liên kết thực đơn, nhật ký, quyết định duyệt mà không cần hiển thị thông tin nhạy cảm.',suggestions:['Dữ liệu có an toàn không?','Tìm hồ sơ bằng ID','ID có thay đổi không?']},
  {keys:/(bao mat|rieng tu|du lieu|luu o dau|chia se)/,answer:'Chatbot này chỉ cung cấp hướng dẫn giao diện và xử lý câu hỏi ngay trên trình duyệt; không gửi nội dung sang dịch vụ AI bên ngoài. Bạn vẫn không nên nhập mật khẩu, số định danh cá nhân hoặc thông tin y tế không cần thiết. Quyền xem dữ liệu phụ thuộc vai trò đăng nhập.',suggestions:['Ai xem được hồ sơ?','Chatbot lưu gì?','Đăng xuất ở đâu?']},
  {keys:/(toi|sang|dark|light|theme|giao dien)/,answer:'Nút mặt trời/mặt trăng chuyển toàn bộ ứng dụng giữa sáng và tối. Lựa chọn được lưu trên trình duyệt. Nếu còn màu cũ sau khi cập nhật phiên bản, hãy tải cứng bằng Ctrl + Shift + R.',suggestions:['Giao diện có chuyển động không?','Cách tắt chuyển động','Màu chưa cập nhật']},
  {keys:/(dynamic|chuyen dong|nhap nhay|animation)/,answer:'Giao diện dùng chuyển động có tiết chế: card xuất hiện nhẹ, hover nâng bề mặt, nút chính có ánh sáng chậm và trạng thái có nhịp pulse. Nếu thiết bị bật Giảm chuyển động, các hiệu ứng sẽ tự tắt để đảm bảo khả năng tiếp cận.',suggestions:['Bật lại chuyển động','Chế độ tối','Hỗ trợ điện thoại']},
  {keys:/(dien thoai|mobile|responsive|man hinh nho)/,answer:'Trên điện thoại, nội dung chuyển thành một cột, nút thao tác mở rộng dễ chạm, sidebar dùng menu di động và chatbot mở dạng bảng từ cạnh phải. Nếu thấy tràn ngang, hãy tải lại bản mới và đặt mức thu phóng trình duyệt về 100%.',suggestions:['Chatbot trên điện thoại','Nội dung bị tràn','Đổi sáng tối']},
  {keys:/(loi|khong duoc|khong thay|bi khoa|khong bam|tai lai|server)/,answer:'Bạn thử theo thứ tự: kiểm tra đang ở đúng vai trò, tải cứng trang bằng Ctrl + Shift + R, đăng nhập lại, rồi kiểm tra kết nối máy chủ. Nút có thể bị khóa khi thiếu hồ sơ, thiếu dữ liệu bắt buộc, đang xử lý hoặc có cảnh báo chặn. Hãy cho mình biết tên màn hình và dòng thông báo để mình chỉ đúng bước.',suggestions:['Không đăng nhập được','Nút tạo bị khóa','Không thấy thực đơn']},
  {keys:/(dau|cap cuu|trieu chung|chan doan|lieu dung|duong huyet|ke don)/,answer:'Mình không thể chẩn đoán, kê đơn, đổi liều thuốc hoặc đánh giá tình trạng cấp cứu. Nếu có triệu chứng nghiêm trọng, phản ứng dị ứng hoặc chỉ số bất thường, hãy liên hệ cơ sở y tế/bác sĩ đang phụ trách ngay. Mình có thể hướng dẫn cách ghi nhận thông tin hoặc tìm chức năng liên hệ trong ứng dụng.',suggestions:['Cách ghi nhận món ăn','Cập nhật thuốc trong hồ sơ','Liên hệ chuyên gia']},
]

function screenHint(path:string){if(path.includes('/meal-plans/new'))return 'Bạn đang ở màn hình tạo thực đơn; mình có thể hướng dẫn chọn hồ sơ, tạo phương án hoặc đọc kiểm tra.';if(path.includes('/food-logs'))return 'Bạn đang ở màn hình đối chiếu nhật ký; mình có thể giải thích món chờ và cách xử lý.';if(path.includes('/reviews'))return 'Bạn đang ở hàng chờ duyệt; mình có thể hướng dẫn xem bằng chứng, duyệt hoặc từ chối.';if(path.includes('/patient/diary'))return 'Bạn đang ở Nhật ký món ăn; mình có thể hướng dẫn ghi món và khẩu phần.';if(path.includes('/patient/weekly'))return 'Bạn đang ở Tổng hợp tuần; mình có thể giải thích từng chỉ số.';if(path.includes('/patient/profile'))return 'Bạn đang ở Hồ sơ; mình có thể giải thích dữ liệu và yêu cầu cập nhật.';return 'Bạn có thể cho mình biết vai trò và thao tác đang muốn thực hiện.'}

function answerFor(input:string,path:string):Reply{
  const text=normalize(input)
  const matches=KNOWLEDGE.filter(item=>item.keys.test(text)).slice(0,2)
  if(matches.length)return{text:matches.map(item=>item.answer).join('\n\n'),suggestions:[...new Set(matches.flatMap(item=>item.suggestions))].slice(0,4)}
  return{text:`Mình chưa xác định chính xác ý bạn. ${screenHint(path)} Mô tả theo mẫu “Tôi đang ở màn hình…, muốn…, nhưng thấy…” để mình hướng dẫn từng bước.`,suggestions:['Hướng dẫn theo màn hình này',...DEFAULT_SUGGESTIONS.slice(0,3)]}
}

// FE-20 (v2, theo yêu cầu trực tiếp): chatbot trước đó nằm trong sidebar (v1) vẫn bị coi là
// "vị trí không phù hợp". Đổi sang mẫu tab kéo ra ở giữa cạnh phải màn hình — cố định, không
// đè lên nội dung (chỉ chiếm dải hẹp ngoài rìa), bấm vào trượt ra thành khung chat toàn chiều
// cao bên phải. Áp dụng thống nhất trên MỌI trang, không phân biệt WorkspaceShell hay không.
type AssistantState={
  theme:Theme
  toggleTheme:()=>void
  open:boolean
  setOpen:(value:boolean|((current:boolean)=>boolean))=>void
}
const AssistantContext=createContext<AssistantState|null>(null)

export function useAssistant(){
  const ctx=useContext(AssistantContext)
  if(!ctx)throw new Error('useAssistant phải dùng trong AssistantProvider')
  return ctx
}

const WORKSPACE_SHELL_PREFIXES=['/patient','/dietitian']

export function AssistantProvider({children}:{children:React.ReactNode}){
  const pathname=usePathname()
  const [theme,setTheme]=useState<Theme>('light')
  const [open,setOpen]=useState(false)
  const [input,setInput]=useState('')
  const [typing,setTyping]=useState(false)
  const [suggestions,setSuggestions]=useState(STARTERS)
  const [messages,setMessages]=useState<Message[]>([{id:1,from:'assistant',text:'Xin chào, mình là trợ lý hướng dẫn VNutriCare. Bạn cần tìm hiểu phần nào?'}])
  const endRef=useRef<HTMLDivElement>(null)

  useEffect(()=>{const timer=window.setTimeout(()=>setTheme(document.documentElement.dataset.theme==='dark'?'dark':'light'),0);return()=>window.clearTimeout(timer)},[])
  useEffect(()=>{endRef.current?.scrollIntoView({behavior:'smooth'})},[messages,typing,open])
  useEffect(()=>{const close=(event:KeyboardEvent)=>{if(event.key==='Escape')setOpen(false)};window.addEventListener('keydown',close);return()=>window.removeEventListener('keydown',close)},[])

  function toggleTheme(){const next=theme==='light'?'dark':'light';setTheme(next);document.documentElement.dataset.theme=next;document.documentElement.style.colorScheme=next;localStorage.setItem('vnutricare_theme',next)}
  function ask(value:string){const question=value.trim();if(!question||typing)return;setMessages(current=>[...current,{id:Date.now(),from:'user',text:question}]);setSuggestions([]);setInput('');setTyping(true);window.setTimeout(()=>{const reply=answerFor(question,window.location.pathname);setMessages(current=>[...current,{id:Date.now()+1,from:'assistant',text:reply.text}]);setSuggestions(reply.suggestions);setTyping(false)},520+Math.min(question.length*5,450))}
  function submit(event:FormEvent){event.preventDefault();ask(input)}

  const inWorkspaceShell=WORKSPACE_SHELL_PREFIXES.some(prefix=>pathname?.startsWith(prefix))

  return <AssistantContext.Provider value={{theme,toggleTheme,open,setOpen}}>
    {children}

    <button type="button" className={`${styles.edgeTab}${open?` ${styles.edgeTabOpen}`:''}`} onClick={()=>setOpen(value=>!value)} aria-expanded={open} aria-controls="assistant-drawer" aria-label={open?'Đóng trợ lý':'Mở trợ lý hướng dẫn'}>
      <Icon name={open?'arrowRight':'robot'}/>
    </button>

    {/* Trang dùng WorkspaceShell đã có nút dark-mode trong sidebar; trang còn lại
        (login, landing, /eval) dùng nút nổi nhỏ này làm phương án dự phòng. */}
    {!inWorkspaceShell&&<button type="button" className={styles.themeFallback} onClick={toggleTheme} aria-label={theme==='light'?'Chuyển sang giao diện tối':'Chuyển sang giao diện sáng'} title={theme==='light'?'Giao diện tối':'Giao diện sáng'}><Icon name={theme==='light'?'moon':'sun'}/></button>}

    {open&&<button type="button" className={styles.drawerBackdrop} aria-label="Đóng trợ lý" onClick={()=>setOpen(false)}/>}
    <section id="assistant-drawer" className={`${styles.chat} ${v2.chat}${open?` ${styles.chatOpen}`:''}`} data-assistant="panel" role="dialog" aria-modal="true" aria-label="Trợ lý hướng dẫn VNutriCare" aria-hidden={!open}>
      <header className={v2.header}><div className={`${styles.botMark} ${v2.botMark}`}><Icon name="sparkles"/><i/></div><div><small className={v2.eyebrow}>VNUTRICARE ASSIST</small><strong>Trợ lý đồng hành</strong><span><i/> Sẵn sàng hướng dẫn</span></div><button type="button" onClick={()=>setOpen(false)} aria-label="Đóng trợ lý"><Icon name="close"/></button></header>
      <div className={`${styles.context} ${v2.context}`} data-assistant="notice"><Icon name="shield"/><span>Hướng dẫn bảo mật · không thay thế tư vấn y khoa</span></div>
      <div className={`${styles.messages} ${v2.messages}`} data-assistant="messages" aria-live="polite">
        {messages.length===1&&<section className={v2.welcome}><div className={v2.welcomeCopy}><span>Xin chào</span><h2>Bạn muốn hoàn thành việc gì?</h2><p>Chọn một chủ đề hoặc đặt câu hỏi bằng ngôn ngữ tự nhiên.</p></div><div className={v2.topicGrid}>{TOPICS.map(topic=><button type="button" key={topic.title} onClick={()=>ask(topic.question)}><span><Icon name={topic.icon}/></span><strong>{topic.title}</strong><small>{topic.text}</small><Icon name="chevronRight"/></button>)}</div></section>}
        {messages.map(message=><div key={message.id} data-from={message.from} className={`${message.from==='assistant'?styles.assistant:styles.user} ${v2.message}`}>{message.from==='assistant'&&<span><Icon name="sparkles"/></span>}<div><small>{message.from==='assistant'?'VN Assistant':'Bạn'}</small><p>{message.text}</p></div></div>)}{typing&&<div className={`${styles.assistant} ${v2.message}`} data-from="assistant"><span><Icon name="sparkles"/></span><div><small>Đang soạn câu trả lời</small><p className={styles.typing}><i/><i/><i/></p></div></div>}<div ref={endRef}/>
      </div>
      {suggestions.length>0&&messages.length>1&&<div className={`${styles.starters} ${v2.starters}`} data-assistant="starters">{suggestions.map(item=><button type="button" key={item} onClick={()=>ask(item)}>{item}<Icon name="arrowRight"/></button>)}</div>}
      <form className={v2.composer} onSubmit={submit}><div><label htmlFor="assistant-question">Đặt câu hỏi cho trợ lý</label><input id="assistant-question" value={input} onChange={event=>setInput(event.target.value)} placeholder="Ví dụ: Vì sao chưa thể duyệt thực đơn?" maxLength={500}/></div><button type="submit" disabled={!input.trim()||typing} aria-label="Gửi câu hỏi"><Icon name="arrowRight"/></button></form>
    </section>
  </AssistantContext.Provider>
}

export function ThemeToggleButton({className}:{className?:string}){
  const {theme,toggleTheme}=useAssistant()
  return <button type="button" className={`${styles.theme} ${className??''}`} onClick={toggleTheme} aria-label={theme==='light'?'Chuyển sang giao diện tối':'Chuyển sang giao diện sáng'} title={theme==='light'?'Giao diện tối':'Giao diện sáng'}><Icon name={theme==='light'?'moon':'sun'}/></button>
}
