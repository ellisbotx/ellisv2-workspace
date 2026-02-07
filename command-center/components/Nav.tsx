import Link from "next/link";

const links = [
  { href: "/", label: "Activity" },
  { href: "/calendar", label: "Calendar" },
  { href: "/search", label: "Search" },
];

export function Nav() {
  return (
    <header className="sticky top-0 z-20 border-b border-white/10 bg-zinc-950/70 backdrop-blur">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <div className="text-sm font-semibold tracking-wide text-zinc-100">
          Marco&apos;s Command Center
        </div>
        <nav className="flex gap-4 text-sm text-zinc-300">
          {links.map((l) => (
            <Link key={l.href} href={l.href} className="hover:text-white">
              {l.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
