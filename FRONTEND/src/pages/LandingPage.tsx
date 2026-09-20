import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ShieldAlert,
  Search,
  UserCheck,
  CheckCircle2,
  ArrowRight,
  Sparkles,
  GitGraph,
  HelpCircle,
  FileText,
  Clock,
  Zap,
} from 'lucide-react';
import { Logo } from '../components/ui/Logo';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Card, CardContent } from '../components/ui/Card';

export const LandingPage: React.FC = () => {
  const scrollToHowTo = () => {
    document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' });
  };

  const steps = [
    {
      num: '01',
      title: 'Log in with the demo account',
      desc: 'Use one-click analyst credentials to enter the secure fraud investigation workspace.',
    },
    {
      num: '02',
      title: 'Pick an alert in Investigations',
      desc: 'Browse flagged high-risk card alerts triaged across velocity, device anomaly, and out-of-region triggers.',
    },
    {
      num: '03',
      title: 'Watch the agent gather graph evidence',
      desc: 'Trigger autonomous graph traversal across multi-hop cardholders, device profiles, and historical closed cases in TigerGraph.',
    },
    {
      num: '04',
      title: 'Answer evidence requests when unsure',
      desc: 'If the agent detects uncertainty, review its prompt and simulate customer SMS confirmation or analyst verification.',
    },
    {
      num: '05',
      title: 'Approve or reject policy actions & read SAR',
      desc: 'Audit policy routing (auto, L1, L2), make one-click decisions, and export formatted Suspicious Activity Reports.',
    },
  ];

  const agentLoop = [
    { step: '1. Trigger', title: 'Alert Ingestion', desc: 'Real-time card transaction flag ingested with risk score & context.' },
    { step: '2. Investigate', title: 'Sub-graph Querying', desc: 'Queries TigerGraph via MCP tools to extract cardholder baselines & velocity.' },
    { step: '3. Gather Evidence', title: 'Multi-Hop Association', desc: 'Discovers shared device profiles, email domains, and coordinated ring entities.' },
    { step: '4. Assess Uncertainty', title: 'Confidence Scoring', desc: 'Calculates fraud probability & identifies conflicting behavioral signals.' },
    { step: '5. Request More Evidence', title: 'Interactive Clarification', desc: 'Dispatches simulated 2FA, cardholder confirmation, or senior analyst prompts.' },
    { step: '6. Take Next Action', title: 'Policy Engine Routing', desc: 'Maps deterministic banking rules (R1-R10) to auto, L1, or L2 approvals.' },
    { step: '7. Explain & File SAR', title: 'Audit Trail Generation', desc: 'Compiles plain-language narrative, timeline audit, and downloadable SAR text.' },
    { step: '8. Update Memory', title: 'Graph Case Persistence', desc: 'Persists findings and embeddings into TigerGraph for future vector matching.' },
  ];

  return (
    <div className="min-h-screen bg-[#FAF9F5] text-[#141413] flex flex-col selection:bg-[#F5E6DF] selection:text-[#D97757]">
      {/* Slim Top Navigation */}
      <header className="sticky top-0 z-40 bg-[#FAF9F5]/90 backdrop-blur-md border-b border-[#E8E6DC] px-6 lg:px-12 py-3.5 flex items-center justify-between">
        <Logo showText={true} />
        <div className="flex items-center gap-6">
          <button
            onClick={scrollToHowTo}
            className="text-xs font-medium text-[#6B6A65] hover:text-[#141413] transition-colors cursor-pointer hidden sm:block"
          >
            How it works
          </button>
          <Link to="/login">
            <Button variant="secondary" size="sm">
              Login to Workspace
            </Button>
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <section className="pt-20 pb-16 px-6 lg:px-12 max-w-5xl mx-auto text-center flex flex-col items-center">
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#F5E6DF] border border-[#E8C5B8] text-xs font-medium text-[#D97757] mb-6"
        >
          <Sparkles className="w-3.5 h-3.5" />
          Autonomous Graph AI Investigation
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="font-serif text-4xl sm:text-5xl lg:text-6xl font-medium tracking-tight text-[#141413] leading-[1.15] max-w-4xl"
        >
          Investigate fraud in minutes, not days.
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="text-base sm:text-lg text-[#6B6A65] mt-6 max-w-2xl font-normal leading-relaxed"
        >
          An AI agent that investigates suspicious card activity using a TigerGraph knowledge graph, asks for more proof when it is unsure, and recommends the next best action within your bank's policy.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="flex flex-wrap items-center justify-center gap-4 mt-8"
        >
          <Link to="/login">
            <Button size="lg" rightIcon={<ArrowRight className="w-4 h-4" />}>
              Get started with demo
            </Button>
          </Link>
          <Button variant="secondary" size="lg" onClick={scrollToHowTo}>
            See how to use it
          </Button>
        </motion.div>
      </section>

      {/* 3 Plain-Language Explainer Cards */}
      <section className="py-12 px-6 lg:px-12 max-w-5xl mx-auto w-full">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card hoverEffect={true} className="p-6">
            <div className="w-10 h-10 rounded-xl bg-[#FBEAE7] text-[#C0392B] flex items-center justify-center mb-4 border border-[#F5C7BE]">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <h3 className="font-serif text-xl font-medium text-[#141413]">An alert is a smoke alarm</h3>
            <p className="text-xs text-[#6B6A65] mt-2 leading-relaxed">
              Rules and ML models flag unusual transactions when risk scores spike. But an alert isn't proof—it is just the trigger to begin investigation.
            </p>
          </Card>

          <Card hoverEffect={true} className="p-6">
            <div className="w-10 h-10 rounded-xl bg-[#F5E6DF] text-[#D97757] flex items-center justify-center mb-4 border border-[#E8C5B8]">
              <Search className="w-5 h-5" />
            </div>
            <h3 className="font-serif text-xl font-medium text-[#141413]">The agent is the detective</h3>
            <p className="text-xs text-[#6B6A65] mt-2 leading-relaxed">
              It connects to TigerGraph, queries cardholder baselines, traces device clusters, checks policy rules, and asks for proof when evidence is ambiguous.
            </p>
          </Card>

          <Card hoverEffect={true} className="p-6">
            <div className="w-10 h-10 rounded-xl bg-[#E6F4EA] text-[#2F855A] flex items-center justify-center mb-4 border border-[#C3E6CB]">
              <UserCheck className="w-5 h-5" />
            </div>
            <h3 className="font-serif text-xl font-medium text-[#141413]">You are the decision-maker</h3>
            <p className="text-xs text-[#6B6A65] mt-2 leading-relaxed">
              The agent handles routine clearances automatically, but surfaces high-risk decisions (L1 & L2) to human fraud analysts with clear reasons and evidence.
            </p>
          </Card>
        </div>
      </section>

      {/* HOW TO USE: 5 Numbered Steps */}
      <section id="how-it-works" className="py-16 px-6 lg:px-12 max-w-5xl mx-auto w-full border-t border-[#E8E6DC]/80">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <Badge variant="terracotta" size="sm" className="mb-3">
            Step-by-Step Workflow
          </Badge>
          <h2 className="font-serif text-3xl sm:text-4xl font-medium text-[#141413]">
            How to use FraudSight Agent
          </h2>
          <p className="text-sm text-[#6B6A65] mt-2">
            Five simple steps to triage, investigate, and resolve complex card fraud cases.
          </p>
        </div>

        <div className="space-y-4">
          {steps.map((step, idx) => (
            <motion.div
              key={step.num}
              initial={{ opacity: 0, y: 15 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: idx * 0.1 }}
            >
              <Card hoverEffect={true} className="p-5 sm:p-6 flex flex-col sm:flex-row items-start sm:items-center gap-5">
                <div className="text-2xl font-serif font-medium text-[#D97757] bg-[#F5E6DF] w-12 h-12 rounded-xl flex items-center justify-center shrink-0 border border-[#E8C5B8]">
                  {step.num}
                </div>
                <div className="flex-1">
                  <h4 className="font-serif text-lg font-medium text-[#141413]">{step.title}</h4>
                  <p className="text-xs text-[#6B6A65] mt-1 leading-relaxed">{step.desc}</p>
                </div>
                <CheckCircle2 className="w-5 h-5 text-[#2F855A]/50 shrink-0 hidden sm:block" />
              </Card>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Approval Levels Explainer */}
      <section className="py-12 px-6 lg:px-12 max-w-5xl mx-auto w-full">
        <Card className="p-6 lg:p-8 bg-white border border-[#E8E6DC]">
          <div className="max-w-2xl mb-6">
            <h3 className="font-serif text-2xl font-medium text-[#141413]">
              What the approval levels mean
            </h3>
            <p className="text-xs text-[#6B6A65] mt-1">
              Every action is mapped deterministically to a strict governance tier based on bank policy rules:
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl border border-[#C3E6CB] bg-[#E6F4EA]/40">
              <div className="flex items-center justify-between mb-2">
                <Badge variant="auto">auto</Badge>
                <Zap className="w-4 h-4 text-[#2F855A]" />
              </div>
              <h4 className="text-sm font-semibold text-[#141413]">The agent acts alone</h4>
              <p className="text-xs text-[#6B6A65] mt-1">
                Low-risk clearances, routine approvals, and automated monitoring for benign false alarms.
              </p>
            </div>

            <div className="p-4 rounded-xl border border-[#F2DCA5] bg-[#FBF1DC]/40">
              <div className="flex items-center justify-between mb-2">
                <Badge variant="L1">L1 Approval</Badge>
                <Clock className="w-4 h-4 text-[#B7791F]" />
              </div>
              <h4 className="text-sm font-semibold text-[#141413]">Analyst approval required</h4>
              <p className="text-xs text-[#6B6A65] mt-1">
                Moderate exposure ($100–$2,500), card locks, and merchant chargeback staging.
              </p>
            </div>

            <div className="p-4 rounded-xl border border-[#F5C7BE] bg-[#FBEAE7]/40">
              <div className="flex items-center justify-between mb-2">
                <Badge variant="L2">L2 Approval</Badge>
                <ShieldAlert className="w-4 h-4 text-[#C0392B]" />
              </div>
              <h4 className="text-sm font-semibold text-[#141413]">Senior supervisor sign-off</h4>
              <p className="text-xs text-[#6B6A65] mt-1">
                High exposure (&gt;$2,500), account closures, law enforcement escalation, and mandatory SAR filing.
              </p>
            </div>
          </div>
        </Card>
      </section>

      {/* The 8-Step Autonomous Loop Animated Timeline */}
      <section className="py-16 px-6 lg:px-12 max-w-5xl mx-auto w-full">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <Badge variant="outline" size="sm" className="mb-3">
            Autonomous Graph Agent Loop
          </Badge>
          <h2 className="font-serif text-3xl sm:text-4xl font-medium text-[#141413]">
            How the agent reasons step-by-step
          </h2>
          <p className="text-sm text-[#6B6A65] mt-2">
            An 8-stage deliberation architecture blending graph traversals, policy rules, and human-in-the-loop interaction.
          </p>
        </div>

        <div className="relative border-l-2 border-[#E8E6DC] ml-4 sm:ml-8 pl-6 sm:pl-8 space-y-8 py-2">
          {agentLoop.map((item, idx) => (
            <motion.div
              key={item.step}
              initial={{ opacity: 0, x: -10 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.35, delay: idx * 0.05 }}
              className="relative"
            >
              {/* Timeline marker */}
              <div className="absolute -left-[31px] sm:-left-[39px] top-1.5 w-4 h-4 rounded-full bg-[#FAF9F5] border-2 border-[#D97757] flex items-center justify-center">
                <div className="w-1.5 h-1.5 rounded-full bg-[#D97757]" />
              </div>

              <div className="bg-white p-4 sm:p-5 rounded-xl border border-[#E8E6DC] shadow-2xs hover:border-[#D5D3C8] transition-colors">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[11px] font-mono font-semibold uppercase text-[#D97757]">
                    {item.step}
                  </span>
                  <span className="text-xs font-semibold text-[#141413]">• {item.title}</span>
                </div>
                <p className="text-xs text-[#6B6A65] leading-relaxed">{item.desc}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Final Call to Action */}
      <section className="py-16 px-6 lg:px-12 max-w-4xl mx-auto w-full text-center">
        <Card className="p-8 sm:p-12 bg-white border border-[#E8E6DC] shadow-sm">
          <h3 className="font-serif text-3xl font-medium text-[#141413]">
            Ready to test live fraud cases?
          </h3>
          <p className="text-sm text-[#6B6A65] mt-2 max-w-md mx-auto">
            Log in with the pre-configured demo account to run graph traversals and policy decisions immediately.
          </p>
          <div className="mt-6 flex justify-center">
            <Link to="/login">
              <Button size="lg" rightIcon={<ArrowRight className="w-4 h-4" />}>
                Continue to login
              </Button>
            </Link>
          </div>
        </Card>
      </section>

      {/* Editorial Footer */}
      <footer className="mt-auto border-t border-[#E8E6DC] py-8 px-6 lg:px-12 text-xs text-[#6B6A65] flex flex-col sm:flex-row items-center justify-between gap-4 max-w-7xl mx-auto w-full">
        <div>
          <span>FraudSight Agent — Graph-powered fraud investigation</span>
        </div>
        <div className="flex items-center gap-6">
          <span>Built for the TigerGraph Hackathon</span>
          <span className="text-[#141413] font-medium">Powered by TigerGraph</span>
        </div>
      </footer>
    </div>
  );
};
