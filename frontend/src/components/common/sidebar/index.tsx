'use client';

import { CollapsibleGroup } from '@/components/tailgrids/core/collapsible';
import { BrandLogo } from '@/components/common/brand-logo';
import { cn } from '@/utils/cn';
import { usePathname } from 'next/navigation';
import { useMemo, useState } from 'react';
import type { Key } from 'react-aria-components';
import { NAV_DATA } from './data';
import { CloseIcon, SidebarExpandedIcon, ThreeDots } from './icon';
import NavItem from './nav-item';
import { findActiveGroupKey } from './utils';

export default function Sidebar({
    isSidebarOpen,
    toggleSidebar,
    isMobileSheet = false,
    onItemClick,
}: {
    isSidebarOpen: boolean;
    toggleSidebar: () => void;
    isMobileSheet?: boolean;
    onItemClick?: () => void;
}) {
    const pathname = usePathname();

    // Compute which group should be open based on the current route
    const activeGroupKey = useMemo(
        () => findActiveGroupKey(pathname),
        [pathname],
    );

    const [expandedKeys, setExpandedKeys] = useState<Set<Key>>(
        () => new Set<Key>(activeGroupKey ? [activeGroupKey] : []),
    );

    return (
        <div className='flex h-full flex-col overflow-hidden bg-background-gray-secondary_alt_2 text-white'>
            {/* Header */}
            <div
                className={cn(
                    'flex items-center px-4 pt-7 text-white',
                    isSidebarOpen
                        ? 'justify-between'
                        : 'flex-col justify-center gap-4',
                )}
            >
                <BrandLogo compact={!isSidebarOpen} />

                <button
                    onClick={() => toggleSidebar()}
                    className={cn(
                        'flex size-11 shrink-0 items-center justify-center transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600',
                        isMobileSheet
                            ? 'rounded-lg text-white/60 hover:bg-white/10 hover:text-white'
                            : 'text-white/60 hover:text-white',
                    )}
                    aria-label={
                        isMobileSheet ? 'Close sidebar' : 'Toggle sidebar'
                    }
                >
                    {isMobileSheet ? <CloseIcon /> : <SidebarExpandedIcon />}
                </button>
            </div>

            {/* Navigation */}
            <nav
                className={cn(
                    'scrollbar-thin flex-1 overflow-y-auto',
                    isSidebarOpen ? 'mt-7 space-y-6 px-4' : 'mt-5 px-2',
                )}
            >
                <CollapsibleGroup
                    expandedKeys={expandedKeys}
                    onExpandedChange={setExpandedKeys}
                >
                    {NAV_DATA.map((section) => (
                        <div key={section.label}>
                            {/* Expanded: show section label | Collapsed: show divider between sections */}
                            {isSidebarOpen ? (
                                <p className='mt-6 mb-4 text-xs uppercase text-white/45'>
                                    {section.label}
                                </p>
                            ) : (
                                section.label && (
                                    <span className='flex items-center justify-center pt-6 pb-4 text-white/45'>
                                        <ThreeDots />
                                    </span>
                                )
                            )}

                            <div
                                className={cn(
                                    'space-y-1',
                                    !isSidebarOpen && 'space-y-1.5',
                                )}
                            >
                                {section.items.map((item) => (
                                    <NavItem
                                        key={item.title}
                                        id={item.title}
                                        icon={item.icon}
                                        label={item.title}
                                        href={item.url}
                                        items={item.items}
                                        collapsed={!isSidebarOpen}
                                        onItemClick={onItemClick}
                                    />
                                ))}
                            </div>
                        </div>
                    ))}
                </CollapsibleGroup>
            </nav>

            {isSidebarOpen && <p className='px-5 py-5 text-xs leading-5 text-white/45'>Secure organization workspace</p>}
        </div>
    );
}
