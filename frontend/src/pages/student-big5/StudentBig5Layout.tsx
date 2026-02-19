import { ReactNode } from 'react';


interface StudentBig5LayoutProps {
    children: ReactNode;
}

export default function StudentBig5Layout({ children }: StudentBig5LayoutProps) {
    return (
        <div className="w-full">
            {children}
        </div>
    );
}
