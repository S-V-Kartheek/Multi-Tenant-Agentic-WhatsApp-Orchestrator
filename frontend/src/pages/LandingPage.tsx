import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { SignInButton, SignUpButton, useAuth } from '@clerk/clerk-react';
import { motion, useScroll, useTransform, AnimatePresence } from 'framer-motion';
import {
  MessageSquare, Bot, Zap, Shield, BarChart3, Users,
  ChevronRight, CheckCircle, Globe, Cpu, ArrowRight, Star, Play,
  Sparkles, TrendingUp, Lock, Layers
} from 'lucide-react';

// ── Animated counter ─────────────────────────────────────────────────────────
function Counter({ target, suffix = '' }: { target: number; suffix?: string }) {
  const [count, setCount] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const hasRun = useRef(false);

  useEffect(() => {
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting && !hasRun.current) {
        hasRun.current = true;
        let start = 0;
        const step = target / 60;
        const timer = setInterval(() => {
          start += step;
          if (start >= target) { setCount(target); clearInterval(timer); }
          else setCount(Math.floor(start));
        }, 16);
      }
    });
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [target]);

  return <span ref={ref}>{count.toLocaleString()}{suffix}</span>;
}

// ── Particle background ───────────────────────────────────────────────────────
function ParticleField() {
  const particles = Array.from({ length: 30 }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    y: Math.random() * 100,
    size: Math.random() * 3 + 1,
    duration: Math.random() * 20 + 15,
    delay: Math.random() * 10,
  }));

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {particles.map((p) => (
        <motion.div
          key={p.id}
          className="absolute rounded-full bg-indigo-500/20"
          style={{ left: `${p.x}%`, top: `${p.y}%`, width: p.size, height: p.size }}
          animate={{ y: [0, -80, 0], opacity: [0, 0.6, 0] }}
          transition={{ duration: p.duration, delay: p.delay, repeat: Infinity, ease: 'easeInOut' }}
        />
      ))}
    </div>
  );
}

// ── Feature card ─────────────────────────────────────────────────────────────
function FeatureCard({ icon: Icon, title, description, gradient, delay }: {
  icon: React.ElementType; title: string; description: string;
  gradient: string; delay: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.6, delay }}
      whileHover={{ y: -6, scale: 1.02 }}
      className="relative group rounded-2xl p-6 bg-white/5 border border-white/10 backdrop-blur-sm cursor-default overflow-hidden"
    >
      <div className={`absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 ${gradient} rounded-2xl`} />
      <div className="relative z-10">
        <div className={`inline-flex p-3 rounded-xl ${gradient} mb-4`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        <h3 className="text-lg font-semibold text-white mb-2">{title}</h3>
        <p className="text-slate-400 text-sm leading-relaxed">{description}</p>
      </div>
    </motion.div>
  );
}

// ── Testimonial card ──────────────────────────────────────────────────────────
function TestimonialCard({ quote, name, role, company, avatar, delay }: {
  quote: string; name: string; role: string; company: string; avatar: string; delay: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.6, delay }}
      className="rounded-2xl p-6 bg-white/5 border border-white/10 backdrop-blur-sm"
    >
      <div className="flex gap-1 mb-4">
        {[...Array(5)].map((_, i) => (
          <Star key={i} className="w-4 h-4 fill-amber-400 text-amber-400" />
        ))}
      </div>
      <p className="text-slate-300 text-sm leading-relaxed mb-4">"{quote}"</p>
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm">
          {avatar}
        </div>
        <div>
          <p className="text-white text-sm font-semibold">{name}</p>
          <p className="text-slate-500 text-xs">{role} · {company}</p>
        </div>
      </div>
    </motion.div>
  );
}

// ── Pricing tier ─────────────────────────────────────────────────────────────
function PricingCard({ tier, price, features, highlighted, delay }: {
  tier: string; price: string; features: string[]; highlighted?: boolean; delay: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.6, delay }}
      className={`relative rounded-2xl p-8 border ${
        highlighted
          ? 'bg-gradient-to-b from-indigo-600/30 to-purple-600/20 border-indigo-500/50 shadow-2xl shadow-indigo-500/20'
          : 'bg-white/5 border-white/10'
      }`}
    >
      {highlighted && (
        <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1.5 rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 text-white text-xs font-semibold">
          Most Popular
        </div>
      )}
      <p className="text-slate-400 text-sm mb-2">{tier}</p>
      <div className="flex items-end gap-1 mb-6">
        <span className="text-4xl font-bold text-white">{price}</span>
        {price !== 'Custom' && <span className="text-slate-400 text-sm mb-1">/month</span>}
      </div>
      <ul className="space-y-3 mb-8">
        {features.map((f, i) => (
          <li key={i} className="flex items-center gap-2.5 text-sm text-slate-300">
            <CheckCircle className="w-4 h-4 text-indigo-400 flex-shrink-0" />
            {f}
          </li>
        ))}
      </ul>
      <SignUpButton>
        <button className={`w-full py-3 rounded-xl font-semibold text-sm transition-all duration-200 ${
          highlighted
            ? 'bg-gradient-to-r from-indigo-500 to-purple-600 text-white hover:shadow-lg hover:shadow-indigo-500/30 hover:scale-105'
            : 'bg-white/10 text-white hover:bg-white/20'
        }`}>
          Get Started Free
        </button>
      </SignUpButton>
    </motion.div>
  );
}

// ── Main Landing Page ─────────────────────────────────────────────────────────
export function LandingPage() {
  const { isSignedIn } = useAuth();
  const navigate = useNavigate();
  const heroRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll();
  const heroY = useTransform(scrollYProgress, [0, 0.3], [0, -80]);
  const heroOpacity = useTransform(scrollYProgress, [0, 0.25], [1, 0]);

  useEffect(() => {
    if (isSignedIn) navigate('/dashboard');
  }, [isSignedIn, navigate]);

  const features = [
    {
      icon: Bot, title: 'LangGraph AI Agent', gradient: 'bg-gradient-to-br from-indigo-600 to-indigo-800',
      description: 'Stateful, multi-step AI conversations powered by Google Gemini Flash 2.0. Handles complex queries with contextual memory across sessions.',
      delay: 0.1,
    },
    {
      icon: Users, title: 'True Multi-Tenancy', gradient: 'bg-gradient-to-br from-purple-600 to-purple-800',
      description: 'Fully isolated tenant environments with per-tenant AI personas, knowledge bases, media catalogs, and conversation histories.',
      delay: 0.2,
    },
    {
      icon: MessageSquare, title: 'WhatsApp Native', gradient: 'bg-gradient-to-br from-emerald-600 to-emerald-800',
      description: 'Direct Twilio integration for WhatsApp messaging. Send text, images, documents, and catalogs—exactly as the user expects.',
      delay: 0.3,
    },
    {
      icon: Zap, title: 'Real-time SSE', gradient: 'bg-gradient-to-br from-amber-600 to-amber-800',
      description: 'Live dashboard updates via Server-Sent Events. Watch conversations unfold in real time without page refreshes.',
      delay: 0.4,
    },
    {
      icon: BarChart3, title: 'Analytics Engine', gradient: 'bg-gradient-to-br from-rose-600 to-rose-800',
      description: 'Deep conversation analytics, agent performance metrics, escalation rates, and response-time tracking per tenant.',
      delay: 0.5,
    },
    {
      icon: Shield, title: 'Enterprise Security', gradient: 'bg-gradient-to-br from-teal-600 to-teal-800',
      description: 'Clerk-powered authentication, encrypted secrets via Render, and strict per-tenant data isolation at every layer.',
      delay: 0.6,
    },
  ];

  const testimonials = [
    { quote: 'Reduced our customer support load by 70% in the first month. The AI handles routine queries flawlessly.', name: 'Sarah Chen', role: 'Head of Customer Experience', company: 'TechFlow', avatar: 'SC', delay: 0.1 },
    { quote: 'Multi-tenant setup was a game-changer for our agency. Each client gets a fully isolated, branded AI assistant.', name: 'Marcus Rodriguez', role: 'CTO', company: 'AgencyPro', avatar: 'MR', delay: 0.2 },
    { quote: 'The LangGraph agent handles context better than any chatbot we\'ve used. It actually remembers what users said.', name: 'Priya Patel', role: 'Product Manager', company: 'RetailNext', avatar: 'PP', delay: 0.3 },
  ];

  return (
    <div className="min-h-screen bg-[#030712] text-white overflow-x-hidden">
      {/* ── Navbar ────────────────────────────────────────────────────────── */}
      <nav className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 md:px-12 py-4 bg-[#030712]/80 backdrop-blur-xl border-b border-white/5">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
            <MessageSquare className="w-4 h-4 text-white" />
          </div>
          <span className="text-lg font-bold text-white">OrchestrAI</span>
          <span className="hidden sm:block px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-400 text-xs font-medium border border-indigo-500/30">WhatsApp</span>
        </div>
        <div className="hidden md:flex items-center gap-8">
          <a href="#features" className="text-sm text-slate-400 hover:text-white transition-colors">Features</a>
          <a href="#how-it-works" className="text-sm text-slate-400 hover:text-white transition-colors">How it works</a>
          <a href="#pricing" className="text-sm text-slate-400 hover:text-white transition-colors">Pricing</a>
        </div>
        <div className="flex items-center gap-3">
          <SignInButton>
            <button className="text-sm text-slate-300 hover:text-white transition-colors px-4 py-2">Sign in</button>
          </SignInButton>
          <SignUpButton>
            <button className="text-sm bg-gradient-to-r from-indigo-500 to-purple-600 text-white px-5 py-2 rounded-xl font-medium hover:opacity-90 transition-opacity shadow-lg shadow-indigo-500/25">
              Get Started
            </button>
          </SignUpButton>
        </div>
      </nav>

      {/* ── Hero ──────────────────────────────────────────────────────────── */}
      <section ref={heroRef} className="relative min-h-screen flex items-center justify-center pt-20">
        <ParticleField />

        {/* Background glows */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-600/20 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-600/15 rounded-full blur-3xl" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-500/5 rounded-full blur-3xl" />
        </div>

        {/* Grid lines */}
        <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%2260%22%20height%3D%2260%22%3E%3Cpath%20d%3D%22M%2060%200%20L%200%200%200%2060%22%20fill%3D%22none%22%20stroke%3D%22rgba(255%2C255%2C255%2C0.03)%22%20stroke-width%3D%221%22%2F%3E%3C%2Fsvg%3E')] opacity-100 pointer-events-none" />

        <motion.div style={{ y: heroY, opacity: heroOpacity }} className="relative z-10 text-center px-6 max-w-5xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-sm font-medium mb-8"
          >
            <Sparkles className="w-4 h-4" />
            Powered by Google Gemini 2.0 Flash + LangGraph
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.1 }}
            className="text-5xl md:text-7xl font-black tracking-tight mb-6 leading-[1.05]"
          >
            Multi-Tenant
            <span className="block bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              WhatsApp Agent
            </span>
            Orchestrator
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="text-xl text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed"
          >
            Deploy intelligent, context-aware AI agents on WhatsApp for multiple businesses—each with its own persona, knowledge base, and analytics—all from a single platform.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16"
          >
            <SignUpButton>
              <button className="group flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-2xl font-semibold text-base hover:opacity-90 transition-all hover:shadow-2xl hover:shadow-indigo-500/30 hover:scale-105 active:scale-100">
                Start for Free
                <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </button>
            </SignUpButton>
            <a
              href="#how-it-works"
              className="flex items-center gap-2 px-8 py-4 bg-white/5 text-white rounded-2xl font-semibold text-base border border-white/10 hover:bg-white/10 transition-all"
            >
              <Play className="w-4 h-4" />
              See how it works
            </a>
          </motion.div>

          {/* Stats row */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.4 }}
            className="flex flex-wrap items-center justify-center gap-8 md:gap-12"
          >
            {[
              { value: 98, suffix: '%', label: 'Uptime SLA' },
              { value: 2, suffix: 'B+', label: 'WhatsApp users reachable' },
              { value: 200, suffix: 'ms', label: 'Avg. response time' },
              { value: 10, suffix: '+', label: 'Tenants supported' },
            ].map(({ value, suffix, label }) => (
              <div key={label} className="text-center">
                <div className="text-3xl font-black text-white">
                  <Counter target={value} suffix={suffix} />
                </div>
                <div className="text-xs text-slate-500 mt-1">{label}</div>
              </div>
            ))}
          </motion.div>
        </motion.div>

        {/* Floating phone mockup */}
        <motion.div
          initial={{ opacity: 0, x: 60 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, delay: 0.5 }}
          className="absolute right-8 top-1/2 -translate-y-1/2 hidden xl:block"
        >
          <div className="w-64 rounded-3xl bg-white/5 border border-white/10 backdrop-blur-sm p-4 shadow-2xl">
            <div className="flex items-center gap-2 mb-3 pb-3 border-b border-white/10">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center text-xs font-bold">W</div>
              <div>
                <p className="text-xs font-semibold text-white">Prestige Living</p>
                <p className="text-[10px] text-emerald-400">● Online</p>
              </div>
            </div>
            {[
              { text: 'Do you have luxury sofas?', user: true },
              { text: 'Yes! Here\'s our premium catalog 📋', user: false },
              { text: 'What are the prices?', user: true },
              { text: 'Sending you the price list now...', user: false },
            ].map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.8 + i * 0.3 }}
                className={`flex mb-2 ${msg.user ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`rounded-xl px-3 py-1.5 text-xs max-w-[80%] ${
                  msg.user ? 'bg-indigo-600 text-white' : 'bg-white/10 text-slate-300'
                }`}>
                  {msg.text}
                </div>
              </motion.div>
            ))}
            <motion.div
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ duration: 1.5, repeat: Infinity }}
              className="flex gap-1 mt-2 px-3"
            >
              {[0, 1, 2].map(i => (
                <div key={i} className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
              ))}
            </motion.div>
          </div>
        </motion.div>
      </section>

      {/* ── Logos strip ────────────────────────────────────────────────────── */}
      <section className="py-12 border-y border-white/5 bg-white/[0.02]">
        <p className="text-center text-slate-600 text-sm font-medium mb-8 uppercase tracking-widest">Built with industry-leading technology</p>
        <div className="flex flex-wrap items-center justify-center gap-10 px-6 opacity-50">
          {['Google Gemini', 'LangGraph', 'FastAPI', 'MongoDB', 'Twilio', 'Clerk', 'React', 'Docker'].map(t => (
            <span key={t} className="text-slate-400 font-semibold text-sm">{t}</span>
          ))}
        </div>
      </section>

      {/* ── Features ──────────────────────────────────────────────────────── */}
      <section id="features" className="py-24 px-6 max-w-6xl mx-auto">
        <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="text-center mb-16">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-purple-500/10 border border-purple-500/30 text-purple-400 text-sm font-medium mb-4">
            <Layers className="w-4 h-4" />
            Everything you need
          </div>
          <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
            Enterprise-grade AI, <br />
            <span className="bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">ready to deploy</span>
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto">
            A complete platform for running AI-powered WhatsApp agents at scale across multiple business tenants.
          </p>
        </motion.div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map(f => <FeatureCard key={f.title} {...f} />)}
        </div>
      </section>

      {/* ── How it works ──────────────────────────────────────────────────── */}
      <section id="how-it-works" className="py-24 px-6 bg-white/[0.02] border-y border-white/5">
        <div className="max-w-5xl mx-auto">
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-sm font-medium mb-4">
              <TrendingUp className="w-4 h-4" />
              The workflow
            </div>
            <h2 className="text-4xl md:text-5xl font-bold text-white">
              From message to <span className="bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent">intelligent response</span>
            </h2>
          </motion.div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {[
              { step: '01', icon: MessageSquare, title: 'User Sends Message', desc: 'Customer messages your WhatsApp number via Twilio Sandbox', color: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/30' },
              { step: '02', icon: Globe, title: 'Webhook Received', desc: 'FastAPI webhook identifies the tenant by phone number', color: 'text-purple-400 bg-purple-500/10 border-purple-500/30' },
              { step: '03', icon: Cpu, title: 'AI Agent Runs', desc: 'LangGraph + Gemini processes the query with tenant context & tools', color: 'text-pink-400 bg-pink-500/10 border-pink-500/30' },
              { step: '04', icon: Zap, title: 'Rich Reply Sent', desc: 'Text, images, or catalogs sent back via Twilio in milliseconds', color: 'text-amber-400 bg-amber-500/10 border-amber-500/30' },
            ].map(({ step, icon: Icon, title, desc, color }, i) => (
              <motion.div
                key={step}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15 }}
                className="relative text-center"
              >
                {i < 3 && (
                  <div className="hidden md:block absolute top-10 left-full w-full h-px bg-gradient-to-r from-white/20 to-transparent z-10" />
                )}
                <div className={`inline-flex w-20 h-20 rounded-2xl border items-center justify-center mb-4 ${color}`}>
                  <Icon className="w-8 h-8" />
                </div>
                <div className="text-xs font-mono text-slate-600 mb-1">{step}</div>
                <h3 className="text-base font-semibold text-white mb-2">{title}</h3>
                <p className="text-slate-500 text-sm">{desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Testimonials ──────────────────────────────────────────────────── */}
      <section className="py-24 px-6 max-w-5xl mx-auto">
        <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="text-center mb-16">
          <h2 className="text-4xl font-bold text-white mb-4">Loved by businesses</h2>
          <p className="text-slate-400">See what teams are saying about OrchestrAI</p>
        </motion.div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {testimonials.map(t => <TestimonialCard key={t.name} {...t} />)}
        </div>
      </section>

      {/* ── Pricing ───────────────────────────────────────────────────────── */}
      <section id="pricing" className="py-24 px-6 bg-white/[0.02] border-y border-white/5">
        <div className="max-w-5xl mx-auto">
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-sm font-medium mb-4">
              <Lock className="w-4 h-4" />
              Simple pricing
            </div>
            <h2 className="text-4xl font-bold text-white mb-4">Start free, scale as you grow</h2>
          </motion.div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <PricingCard tier="Starter" price="$0" delay={0.1} features={['2 Tenants', '500 messages/month', 'WhatsApp + Twilio', 'Basic analytics', 'Community support']} />
            <PricingCard tier="Professional" price="$49" highlighted delay={0.2} features={['10 Tenants', '10,000 messages/month', 'Custom AI personas', 'Media catalog support', 'Real-time dashboard', 'Priority support']} />
            <PricingCard tier="Enterprise" price="Custom" delay={0.3} features={['Unlimited tenants', 'Unlimited messages', 'Custom LLM integration', 'SLA guarantee', 'Dedicated support', 'On-premise option']} />
          </div>
        </div>
      </section>

      {/* ── CTA ───────────────────────────────────────────────────────────── */}
      <section className="py-32 px-6 text-center">
        <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} className="max-w-3xl mx-auto">
          <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
            <div className="w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl" />
          </div>
          <h2 className="text-5xl font-black text-white mb-6 relative">
            Ready to automate your <br />
            <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">WhatsApp support?</span>
          </h2>
          <p className="text-slate-400 text-lg mb-10">Join hundreds of businesses using OrchestrAI to deliver instant, intelligent WhatsApp responses at scale.</p>
          <SignUpButton>
            <button className="group inline-flex items-center gap-3 px-10 py-5 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-2xl font-bold text-lg hover:opacity-90 transition-all hover:shadow-2xl hover:shadow-indigo-500/40 hover:scale-105 active:scale-100">
              Get started for free
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
          </SignUpButton>
          <p className="text-slate-600 text-sm mt-4">No credit card required · Free forever plan available</p>
        </motion.div>
      </section>

      {/* ── Footer ────────────────────────────────────────────────────────── */}
      <footer className="border-t border-white/5 py-10 px-6">
        <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <MessageSquare className="w-3 h-3 text-white" />
            </div>
            <span className="text-slate-400 text-sm font-medium">OrchestrAI · Multi-Tenant WhatsApp Agent Platform</span>
          </div>
          <p className="text-slate-600 text-xs">Built with ♥ by S V Kartheek · SRMAP University · 2026</p>
        </div>
      </footer>
    </div>
  );
}
