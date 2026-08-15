import { Icon } from '@/components/brand-artwork'
import styles from './patient-avatar.module.css'

export function PatientAvatar({sex,size='md'}:{sex:'male'|'female';size?:'sm'|'md'|'lg'}){
  const label=sex==='male'?'Nam':'Nữ'
  return <span className={styles.avatar} data-sex={sex} data-size={size} role="img" aria-label={`Bệnh nhân ${label}`} title={`Giới tính: ${label}`}>
    <Icon name="user"/>
    <b aria-hidden="true">{sex==='male'?'♂':'♀'}</b>
  </span>
}
