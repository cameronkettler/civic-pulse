import Link from "next/link";
import {
  ArrowLeft,
  Bell,
  BrainCircuit,
  FileSearch,
  MapPinned,
  Radar,
  ShieldCheck,
  UserRound,
} from "lucide-react";

const steps = [
  {
    title: "Search a bill",
    icon: <FileSearch size={18} aria-hidden="true" />,
    text: "Enter a bill number like HR-22 or a plain-language query. The app resolves the bill, pulls official data, and builds a structured political read.",
  },
  {
    title: "Save your address",
    icon: <MapPinned size={18} aria-hidden="true" />,
    text: "Add a street address in Profile so the app can identify your House district and two senators. ZIP alone is not always precise enough.",
  },
  {
    title: "Read representative context",
    icon: <UserRound size={18} aria-hidden="true" />,
    text: "Reports check sponsor, cosponsor, vote, and public-source signals to show how your representatives connect to the bill.",
  },
  {
    title: "Run a deep dive",
    icon: <BrainCircuit size={18} aria-hidden="true" />,
    text: "Representative Deep Dive summarizes public themes, recent legislation, campaign-finance context, and election status for your members.",
  },
  {
    title: "Tune your watchlist",
    icon: <Bell size={18} aria-hidden="true" />,
    text: "Watchlist topics shape monitoring, recent bill prompts, and representative deep-dive alignment.",
  },
];

export default function AboutPage() {
  return (
    <main className="min-h-screen bg-[#eef1f4] text-ink">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded bg-civic text-white">
              <Radar size={21} aria-hidden="true" />
            </div>
            <div>
              <h1 className="text-xl font-semibold tracking-normal">How Congress For Normal People Works</h1>
              <p className="text-sm text-slate-600">A quick guide to reports, profiles, and deep dives.</p>
            </div>
          </div>
          <Link
            href="/"
            className="focus-ring inline-flex items-center gap-2 rounded border border-line px-3 py-2 text-sm font-medium"
          >
            <ArrowLeft size={15} aria-hidden="true" />
            Dashboard
          </Link>
        </div>
      </header>

      <section className="mx-auto grid max-w-5xl gap-5 px-5 py-5">
        <section className="rounded border border-line bg-white p-5">
          <div className="mb-3 flex items-center gap-2">
            <ShieldCheck size={19} aria-hidden="true" />
            <h2 className="text-base font-semibold">What It Solves</h2>
          </div>
          <p className="max-w-3xl text-sm leading-6 text-slate-700">
            Federal bills are public, but understanding them usually means bouncing between Congress.gov,
            vote records, campaign-finance filings, lobbying disclosures, representative websites, and news.
            This app turns that research into a plain-English starting point with source-grounded context.
          </p>
        </section>

        <section className="grid gap-3 md:grid-cols-2">
          {steps.map((step) => (
            <article key={step.title} className="rounded border border-line bg-white p-4">
              <div className="mb-2 flex items-center gap-2 text-sm font-semibold">
                {step.icon}
                {step.title}
              </div>
              <p className="text-sm leading-6 text-slate-700">{step.text}</p>
            </article>
          ))}
        </section>

        <section className="rounded border border-line bg-white p-5">
          <h2 className="text-base font-semibold">How To Read The AI Sections</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-700">
            Official records are treated as strongest evidence: sponsorship, cosponsorship, recorded votes,
            member data, and filings. AI-assisted sections summarize public sources and explain likely context,
            but they should be read as research help, not as a replacement for official records.
          </p>
        </section>
      </section>
    </main>
  );
}
