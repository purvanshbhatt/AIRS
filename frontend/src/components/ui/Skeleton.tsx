import { clsx } from 'clsx';

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
}

export function Skeleton({
  className,
  variant = 'text',
  width,
  height,
}: SkeletonProps) {
  return (
    <div
      className={clsx(
        'animate-pulse bg-gray-200 dark:bg-gray-700',
        variant === 'text' && 'h-4 rounded',
        variant === 'circular' && 'rounded-full',
        variant === 'rectangular' && 'rounded-lg',
        className
      )}
      style={{
        width: typeof width === 'number' ? `${width}px` : width,
        height: typeof height === 'number' ? `${height}px` : height,
      }}
    />
  );
}

// Pre-built skeleton patterns for common use cases
export function CardSkeleton() {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6 space-y-4">
      <div className="flex items-center gap-3">
        <Skeleton variant="circular" width={40} height={40} />
        <div className="flex-1 space-y-2">
          <Skeleton width="60%" height={16} />
          <Skeleton width="40%" height={12} />
        </div>
      </div>
      <Skeleton width="100%" height={12} />
      <Skeleton width="80%" height={12} />
    </div>
  );
}

export function TableRowSkeleton({ columns = 4 }: { columns?: number }) {
  return (
    <tr className="border-b border-gray-100 dark:border-gray-700">
      {Array.from({ length: columns }).map((_, i) => (
        <td key={i} className="py-4 px-4">
          <Skeleton width={i === 0 ? '80%' : '60%'} height={14} />
        </td>
      ))}
    </tr>
  );
}

export function ListSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  );
}

export function StatCardSkeleton() {
  return (
    <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
      <Skeleton width={80} height={12} className="mb-2" />
      <Skeleton width={60} height={32} className="mb-1" />
      <Skeleton width={100} height={10} />
    </div>
  );
}

// Results page skeletons
export function ResultsOverviewSkeleton() {
  return (
    <div className="space-y-6">
      {/* Score card */}
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-8">
        <div className="flex flex-col lg:flex-row items-center justify-center gap-8 lg:gap-16">
          <Skeleton variant="circular" width={192} height={192} />
          <div className="space-y-4">
            <Skeleton width={120} height={16} />
            <Skeleton width={180} height={40} />
            <div className="flex gap-4">
              <Skeleton width={100} height={60} className="rounded-lg" />
              <Skeleton width={100} height={60} className="rounded-lg" />
              <Skeleton width={100} height={60} className="rounded-lg" />
            </div>
          </div>
        </div>
      </div>
      {/* Domain scores */}
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <Skeleton width={150} height={24} className="mb-4" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {[1, 2, 3, 4, 5].map((i) => (
            <Skeleton key={i} height={100} className="rounded-xl" />
          ))}
        </div>
      </div>
    </div>
  );
}

export function ResultsTabSkeleton() {
  return (
    <div className="space-y-4">
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
        <Skeleton width={200} height={24} className="mb-4" />
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="p-4 border border-gray-100 dark:border-gray-700 rounded-lg">
              <div className="flex items-center gap-3 mb-2">
                <Skeleton width={80} height={24} className="rounded-full" />
                <Skeleton width={100} height={16} />
              </div>
              <Skeleton width="90%" height={14} />
              <Skeleton width="60%" height={14} className="mt-2" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function ResultsFrameworkSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center gap-3 mb-4">
              <Skeleton variant="circular" width={40} height={40} />
              <div>
                <Skeleton width={100} height={14} />
                <Skeleton width={60} height={24} className="mt-1" />
              </div>
            </div>
            <Skeleton width="80%" height={12} />
          </div>
        ))}
      </div>
      <CardSkeleton />
    </div>
  );
}

export function ResultsAnalyticsSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <Skeleton width={150} height={24} className="mb-4" />
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="flex items-center gap-3">
                <Skeleton variant="circular" width={32} height={32} />
                <Skeleton width="80%" height={40} className="rounded-lg" />
              </div>
            ))}
          </div>
        </div>
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <Skeleton width={150} height={24} className="mb-4" />
          <div className="space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} height={60} className="rounded-lg" />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
