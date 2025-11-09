'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Upload, Settings, Home } from 'lucide-react'
import { cn } from '@/lib/utils'

export function Navbar() {
	const pathname = usePathname()

	const navItems = [
		{ href: '/', label: 'Загрузки', icon: Upload },
		{ href: '/integrations', label: 'Интеграции', icon: Settings },
	]

	return (
		<nav className="border-b border-gray-200 bg-white">
			<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
				<div className="flex items-center justify-between h-16">
					<div className="flex items-center space-x-8">
						<Link href="/" className="flex items-center space-x-2">
							<span className="text-xl font-semibold text-gray-900">Creo Manager</span>
						</Link>
						<div className="flex items-center space-x-1">
							{navItems.map((item) => {
								const Icon = item.icon
								const isActive = pathname === item.href
								return (
									<Link
										key={item.href}
										href={item.href}
										className={cn(
											'inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors',
											isActive
												? 'bg-primary/10 text-primary'
												: 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
										)}
									>
										<Icon className="h-4 w-4 mr-2" />
										{item.label}
									</Link>
								)
							})}
						</div>
					</div>
				</div>
			</div>
		</nav>
	)
}



