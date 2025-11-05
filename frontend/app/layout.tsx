import type { Metadata } from 'next'
import './globals.css'
import { Providers } from './providers'

export const metadata: Metadata = {
	title: 'Creo Manager',
	description: 'Платформа для управления креативами и загрузки видео на YouTube',
}

export default function RootLayout({
	children,
}: {
	children: React.ReactNode
}) {
	return (
		<html lang="ru">
			<body>
				<Providers>{children}</Providers>
			</body>
		</html>
	)
}

