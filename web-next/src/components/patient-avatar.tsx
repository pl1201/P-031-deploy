import { Icon } from '@/components/brand-artwork'

const BOX_SIZE = { sm: 'w-11 h-11', md: 'w-14 h-14', lg: 'w-[68px] h-[68px]' } as const

export function PatientAvatar({sex,size='md'}:{sex:'male'|'female';size?:'sm'|'md'|'lg'}){
  const label=sex==='male'?'Nam':'Nữ'
  const male=sex==='male'
  return <span
    className={`relative grid flex-none place-items-center rounded-full border ${BOX_SIZE[size]} ${male?'border-[#c9e1de] bg-[#e4f4f2] text-[#087e81]':'border-[#ead3dc] bg-[#f8eaf0] text-[#9b526b]'}`}
    role="img" aria-label={`Bệnh nhân ${label}`} title={`Giới tính: ${label}`}
  >
    <Icon name="user" className="h-[27px] w-[27px] stroke-[1.7]"/>
    <b aria-hidden="true" className={`absolute -right-0.5 -bottom-0.5 grid h-5 w-5 place-items-center rounded-full border-2 border-white text-xs font-normal leading-none text-white not-italic ${male?'bg-[#168f92]':'bg-[#b65d7b]'}`}>{male?'♂':'♀'}</b>
  </span>
}
