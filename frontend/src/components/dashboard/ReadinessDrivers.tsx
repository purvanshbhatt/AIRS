import React, { useState } from 'react';
import { TrendingUp, TrendingDown, ShieldCheck, HelpCircle, ArrowRight } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, Badge } from '../ui';
import { ReadinessDriver, ExecutiveAction } from '../../api';
import SlideOver from '../common/SlideOver';

interface ReadinessDriversProps {
  drivers: {
    positive_drivers: ReadinessDriver[];
    negative_drivers: ReadinessDriver[];
  } | null;
  actions: ExecutiveAction[];
  isLoading: boolean;
  error: string | null;
  onRetry?: () => void;
}

export function ReadinessDrivers({
  drivers,
  actions,
  isLoading,
  error,
  onRetry,
}: ReadinessDriversProps) {
  const [selectedDriver, setSelectedDriver] = useState<ReadinessDriver | null>(null);
  const [isSlideOverOpen, setIsSlideOverOpen] = useState(false);

  const handleDriverClick = (driver: ReadinessDriver) => {
    setSelectedDriver(driver);
    setIsSlideOverOpen(true);
  };

  const getDriverIcon = (driverType: string) => {
    switch (driverType.toLowerCase()) {
      case 'coverage_gap':
      case 'control_gap':
        return <ShieldCheck className="h-4 w-4 text-amber-500" />;
      default:
        return <HelpCircle className="h-4 w-4 text-slate-400" />;
    }
  };

  const formatImpact = (val: number) => {
    const sign = val > 0 ? '+' : '';
    return `${sign}${val.toFixed(1)}`;
  };

  // Find matching action rationale if available
  const getRationaleForDriver = (driver: ReadinessDriver | null) => {
    if (!driver) return null;
    const match = actions.find(
      a => a.driver_type === driver.driver_type && a.item === driver.driver_item
    );
    return match ? match.rationale : `Remediation of this driver will directly improve readiness by ${Math.abs(driver.impact).toFixed(1)} points.`;
  };

  if (isLoading) {
    return (
      <Card className="bg-white/60 dark:bg-slate-900/60 backdrop-blur-[10px] border border-slate-200 dark:border-slate-800">
        <CardHeader>
          <CardTitle className="text-base font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-primary-500" />
            Readiness Impact Drivers
          </CardTitle>
        </CardHeader>
        <CardContent className="h-64 flex flex-col items-center justify-center space-y-3">
          <svg className="animate-spin h-8 w-8 text-primary-500" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <p className="text-sm text-slate-500 dark:text-slate-400 font-medium">Extracting impact drivers...</p>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="bg-white/60 dark:bg-slate-900/60 backdrop-blur-[10px] border border-slate-200 dark:border-slate-800">
        <CardHeader>
          <CardTitle className="text-base font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-primary-500" />
            Readiness Impact Drivers
          </CardTitle>
        </CardHeader>
        <CardContent className="h-64 flex flex-col items-center justify-center text-center px-4 space-y-4">
          <div className="p-2.5 bg-danger-500/10 rounded-full">
            <TrendingDown className="h-6 w-6 text-danger-500" />
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">Failed to load drivers</p>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{error}</p>
          </div>
          {onRetry && (
            <button 
              onClick={onRetry} 
              className="px-3 py-1.5 bg-slate-100 hover:bg-slate-250 dark:bg-slate-800 dark:hover:bg-slate-700 text-xs font-semibold text-slate-900 dark:text-slate-100 rounded-lg transition-colors"
            >
              Retry
            </button>
          )}
        </CardContent>
      </Card>
    );
  }

  const hasDrivers = drivers && (drivers.positive_drivers.length > 0 || drivers.negative_drivers.length > 0);

  if (!hasDrivers) {
    return (
      <Card className="bg-white/60 dark:bg-slate-900/60 backdrop-blur-[10px] border border-slate-200 dark:border-slate-800">
        <CardHeader>
          <CardTitle className="text-base font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-primary-500" />
            Readiness Impact Drivers
          </CardTitle>
        </CardHeader>
        <CardContent className="h-64 flex flex-col items-center justify-center text-center px-4">
          <p className="text-sm text-slate-500 dark:text-slate-400 font-medium">No impact drivers registered.</p>
          <p className="text-xs text-slate-450 dark:text-slate-500 mt-1">Connect telemetry sources or complete an assessment to populate drivers.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card className="bg-white/60 dark:bg-slate-900/60 backdrop-blur-[10px] border border-slate-200 dark:border-slate-800 hover:shadow-md transition-all duration-300">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-2 tracking-tight">
              <TrendingUp className="h-5 w-5 text-[#00C853]" />
              Readiness Impact Drivers
            </CardTitle>
            <Badge className="bg-[#00C853]/10 text-[#00C853] border-[#00C853]/20 text-[9px] font-bold">
              DETERMINISTIC
            </Badge>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-semibold mt-1">
            Top factors affecting your real-time governance score. Click a driver for details.
          </p>
        </CardHeader>
        
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-2">
            {/* Positive Drivers */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-wider">
                <TrendingUp className="h-4 w-4 text-[#00C853]" />
                Positive Contributors
              </div>
              <div className="space-y-2">
                {drivers?.positive_drivers.length === 0 ? (
                  <p className="text-xs text-slate-500 dark:text-slate-400 italic py-2">No positive drivers found.</p>
                ) : (
                  drivers?.positive_drivers.map((drv, idx) => (
                    <div
                      key={`pos-${idx}`}
                      onClick={() => handleDriverClick(drv)}
                      className="p-3 rounded-xl bg-slate-50/50 dark:bg-slate-800/30 border border-slate-200/50 dark:border-slate-800/40 hover:border-[#00C853]/30 dark:hover:border-[#00C853]/30 cursor-pointer flex items-center justify-between transition-all duration-200"
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-1.5 bg-[#00C853]/10 rounded-lg">
                          <TrendingUp className="h-3.5 w-3.5 text-[#00C853]" />
                        </div>
                        <div className="text-left">
                          <p className="text-xs font-bold text-slate-900 dark:text-slate-100 capitalize">
                            {drv.driver_type.replace('_', ' ')}
                          </p>
                          <p className="text-[10px] text-slate-500 dark:text-slate-400 truncate max-w-[150px]">
                            {drv.driver_item || 'Global Score'}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-[#00C853]">
                          {formatImpact(drv.impact)}
                        </span>
                        <ArrowRight className="h-3 w-3 text-slate-400" />
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Negative Drivers */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-wider">
                <TrendingDown className="h-4 w-4 text-[#D97706]" />
                Top Vulnerabilities / Gaps
              </div>
              <div className="space-y-2">
                {drivers?.negative_drivers.length === 0 ? (
                  <p className="text-xs text-slate-500 dark:text-slate-400 italic py-2">No negative drivers found.</p>
                ) : (
                  drivers?.negative_drivers.map((drv, idx) => (
                    <div
                      key={`neg-${idx}`}
                      onClick={() => handleDriverClick(drv)}
                      className="p-3 rounded-xl bg-slate-50/50 dark:bg-slate-800/30 border border-slate-200/50 dark:border-slate-800/40 hover:border-[#D97706]/30 dark:hover:border-[#D97706]/30 cursor-pointer flex items-center justify-between transition-all duration-200"
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-1.5 bg-[#D97706]/10 rounded-lg">
                          <TrendingDown className="h-3.5 w-3.5 text-[#D97706]" />
                        </div>
                        <div className="text-left">
                          <p className="text-xs font-bold text-slate-900 dark:text-slate-100 capitalize">
                            {drv.driver_type.replace('_', ' ')}
                          </p>
                          <p className="text-[10px] text-slate-500 dark:text-slate-400 truncate max-w-[150px]">
                            {drv.driver_item || 'Global Score'}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-danger-500">
                          {formatImpact(drv.impact)}
                        </span>
                        <ArrowRight className="h-3 w-3 text-slate-400" />
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* SlideOver for Driver Details */}
      <SlideOver
        isOpen={isSlideOverOpen}
        onClose={() => setIsSlideOverOpen(false)}
        title="Impact Driver Audit Trail"
      >
        {selectedDriver && (
          <div className="space-y-6 text-left">
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-200/65 dark:border-slate-800 flex items-center justify-between">
              <div>
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">DRIVER CATEGORY</span>
                <span className="text-sm font-black text-slate-900 dark:text-slate-100 capitalize mt-0.5 block">
                  {selectedDriver.driver_type.replace('_', ' ')}
                </span>
              </div>
              <Badge 
                className={selectedDriver.impact > 0 
                  ? "bg-[#00C853]/10 text-[#00C853] border-[#00C853]/20" 
                  : "bg-danger-500/10 text-danger-500 border-danger-500/20"
                }
              >
                {formatImpact(selectedDriver.impact)}
              </Badge>
            </div>

            <div className="space-y-4">
              <div>
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Affected Asset / Control</h4>
                <p className="text-sm font-semibold text-slate-900 dark:text-slate-100 mt-1 font-mono bg-slate-100 dark:bg-slate-900/60 p-2 rounded border border-slate-200/50 dark:border-slate-800/40">
                  {selectedDriver.driver_item || 'Entire Organization'}
                </p>
              </div>

              <div>
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Evidence Source</h4>
                <div className="flex items-center gap-2 mt-1.5">
                  <Badge variant="outline" className="text-[10px] font-mono tracking-wider font-semibold capitalize">
                    {selectedDriver.evidence_source}
                  </Badge>
                </div>
              </div>

              <div className="pt-4 border-t border-slate-200 dark:border-slate-800">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">Remediation Rationale</h4>
                <p className="text-xs text-slate-650 dark:text-slate-400 leading-relaxed bg-[#00C853]/5 dark:bg-[#00C853]/5 border border-[#00C853]/10 dark:border-[#00C853]/10 rounded-xl p-3">
                  {getRationaleForDriver(selectedDriver)}
                </p>
              </div>
            </div>
          </div>
        )}
      </SlideOver>
    </>
  );
}

export default ReadinessDrivers;
