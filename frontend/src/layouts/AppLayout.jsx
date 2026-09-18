import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { Activity, Bell, ClipboardList, Eye, LayoutDashboard, LogOut, Menu, ScanEye, Settings, ShieldCheck, Users, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';

export default function AppLayout() {
	const [open, setOpen] = useState(false);
	const [topbarHidden, setTopbarHidden] = useState(false);
	const { user, logout } = useAuth();
	const navigate = useNavigate();

	useEffect(() => {
		let previousScrollY = window.scrollY;

		function handleScroll() {
			const currentScrollY = window.scrollY;
			const scrollingDown = currentScrollY > previousScrollY;

			setTopbarHidden(currentScrollY > 72 && scrollingDown);
			previousScrollY = currentScrollY;
		}

		window.addEventListener('scroll', handleScroll, { passive: true });
		return () => window.removeEventListener('scroll', handleScroll);
	}, []);

	const links = [
		['/', 'Dashboard', LayoutDashboard],
		['/screening/new', 'New screening', ScanEye],
		['/patients', 'Patients', Users],
		['/history', 'Screening history', ClipboardList],
		...(user?.role === 'admin' ? [['/admin', 'Administration', Settings]] : []),
	];

	return (
		<div className="app-shell">
			<aside className={`sidebar ${open ? 'open' : ''}`}>
				<div className="brand">
					<span className="brand-mark"><Activity size={20} /></span>
					<span>
						<b>DR Vision AI</b>
						<small>PHC screening platform</small>
					</span>
					<button className="icon-button mobile-close" onClick={() => setOpen(false)} aria-label="Close menu">
						<X size={18} />
					</button>
				</div>

				<div className="nav-summary">
					<span className="nav-summary-label">Operations</span>
					<strong>Care coordination</strong>
					<small>12 active screening cases</small>
				</div>

				<p className="nav-label">Workspace</p>
				<nav className="nav-menu">
					{links.map(([to, label, Icon]) => (
						<NavLink
							key={label}
							to={to}
							end={to === '/'}
							onClick={() => setOpen(false)}
							className={({ isActive }) => isActive ? 'nav-pill active' : 'nav-pill'}
						>
							<span className="nav-icon"><Icon size={18} /></span>
							<span>{label}</span>
						</NavLink>
					))}
				</nav>

				<div className="sidebar-bottom">
					<div className="system-status-card">
						<span className="status-dot" />
						<div>
							<strong>AI system online</strong>
							<small>Last sync 46s ago</small>
						</div>
					</div>

					<button
						className="logout-link"
						onClick={() => {
							logout();
							navigate('/login');
						}}
					>
						<LogOut size={17} />
						Sign out
					</button>
				</div>
			</aside>

			<div className="main-shell">
				<header className={`topbar ${topbarHidden ? 'topbar-hidden' : ''}`}>
					<button className="icon-button menu-button" onClick={() => setOpen(true)} aria-label="Open menu">
						<Menu size={21} />
					</button>

					<div className="topbar-copy">
						<div className="topbar-heading">
							<div>
								<span className="eyebrow">PHC RAMPUR / WORKSPACE</span>
								<h1>Clinical screening workspace</h1>
							</div>
							<span className="live-status"><span className="status-dot" /> Live</span>
						</div>
					</div>

					<div className="topbar-actions">
						<div className="privacy-status"><span className="privacy-icon"><Eye size={15} /><ShieldCheck size={10} /></span><span>Protected workspace</span></div>
						<button className="icon-button notification-button" aria-label="View notifications">
							<Bell size={18} />
							<span className="notification-dot" />
						</button>
						<span className="topbar-divider" />
					</div>

					<div className="user-chip">
						<span className="avatar">
							{user?.full_name?.split(' ').map((part) => part[0]).join('').slice(0, 2) || 'PH'}
						</span>
						<span>
							<b>{user?.full_name || 'Healthcare worker'}</b>
							<small>{user?.employee_id || 'Staff account'} · PHC staff</small>
						</span>
					</div>
				</header>

				<main className="content">
					<Outlet />
				</main>
			</div>
		</div>
	);
}
