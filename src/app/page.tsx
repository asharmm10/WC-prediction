import { redirect } from 'next/navigation'

export default function Home() {
  redirect('/?XTransformPort=8000')
}
