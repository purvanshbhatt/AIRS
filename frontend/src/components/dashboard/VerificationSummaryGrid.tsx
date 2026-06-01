import { CheckCircle2, ShieldAlert, FileText, XCircle } from 'lucide-react';
import { Card, CardContent, Badge } from '../ui';

interface VerificationSummaryGridProps {
  verified: number;
  partiallyVerified: number;
  selfAttested: number;
  notVerified: number;
}

export default function VerificationSummaryGrid({
  verified,
  partiallyVerified,
  selfAttested,
  notVerified,
}: VerificationSummaryGridProps) {
  const cards = [
    {
      title: 'Verified Telemetry',
      count: verified,
      badgeColor: 'bg-[#00C853]/10 text-[#00C853] border-[#00C853]/20',
      icon: CheckCircle2,
      iconColor: 'text-[#00C853]',
      description: 'Controls mathematically validated via continuous SIEM agents or webhook events.',
    },
    {
      title: 'Partially Verified',
      count: partiallyVerified,
      badgeColor: 'bg-indigo-500/10 text-indigo-500 border-indigo-500/20',
      icon: ShieldAlert,
      iconColor: 'text-indigo-500',
      description: 'Telemetry streams are connected but rules configurations are not fully aligned.',
    },
    {
      title: 'Self-Attested',
      count: selfAttested,
      badgeColor: 'bg-amber-500/10 text-[#D97706] border-amber-500/20',
      icon: FileText,
      iconColor: 'text-[#D97706]',
      description: 'Attestations manually submitted via self-assessment forms without telemetry logs.',
    },
    {
      title: 'Not Verified',
      count: notVerified,
      badgeColor: 'bg-rose-500/10 text-rose-500 border-rose-500/20',
      icon: XCircle,
      iconColor: 'text-rose-500',
      description: 'Out of scope or unassessed controls requiring checklist configuration mappings.',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 text-left">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <Card 
            key={idx} 
            className="bg-white/60 dark:bg-slate-950/20 backdrop-blur-[10px] border border-slate-200 dark:border-slate-800 rounded-3xl hover:shadow-md transition-all duration-300 relative overflow-hidden"
          >
            <CardContent className="p-5 flex flex-col justify-between h-full space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-slate-500 dark:text-slate-450 font-bold uppercase tracking-wider">
                  {card.title}
                </span>
                <Badge className={`${card.badgeColor} border text-[9px] font-bold`}>
                  STATUS
                </Badge>
              </div>
              
              <div className="flex items-center gap-3">
                <Icon className={`w-8 h-8 ${card.iconColor}`} />
                <h3 className="text-4xl font-extrabold text-slate-900 dark:text-slate-100 tracking-tight">
                  {card.count}
                </h3>
              </div>

              <p className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 leading-normal">
                {card.description}
              </p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
