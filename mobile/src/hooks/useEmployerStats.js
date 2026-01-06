import { useCallback, useEffect, useMemo, useState } from 'react';
import Apis from '../utils/Apis';

// period: 'month' | 'quarter' | 'year'
export default function useEmployerStats({ period, year }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // mock data fallback (MVP)
  const mock = useMemo(() => {
    const baseSeries =
      period === 'month'
        ? [
            { label: 'Jan', applications: 18, shortlistedRate: 0.28, avgScore: 74, postEffect: 0.62 },
            { label: 'Feb', applications: 22, shortlistedRate: 0.31, avgScore: 76, postEffect: 0.65 },
            { label: 'Mar', applications: 15, shortlistedRate: 0.26, avgScore: 71, postEffect: 0.58 },
            { label: 'Apr', applications: 26, shortlistedRate: 0.33, avgScore: 78, postEffect: 0.68 },
            { label: 'May', applications: 30, shortlistedRate: 0.35, avgScore: 80, postEffect: 0.72 },
            { label: 'Jun', applications: 24, shortlistedRate: 0.29, avgScore: 75, postEffect: 0.63 },
          ]
        : period === 'quarter'
        ? [
            { label: 'Q1', applications: 55, shortlistedRate: 0.29, avgScore: 74, postEffect: 0.62 },
            { label: 'Q2', applications: 80, shortlistedRate: 0.34, avgScore: 79, postEffect: 0.70 },
            { label: 'Q3', applications: 63, shortlistedRate: 0.30, avgScore: 77, postEffect: 0.66 },
            { label: 'Q4', applications: 71, shortlistedRate: 0.32, avgScore: 78, postEffect: 0.68 },
          ]
        : [
            { label: String(year - 2), applications: 210, shortlistedRate: 0.28, avgScore: 73, postEffect: 0.60 },
            { label: String(year - 1), applications: 265, shortlistedRate: 0.31, avgScore: 76, postEffect: 0.66 },
            { label: String(year), applications: 298, shortlistedRate: 0.33, avgScore: 78, postEffect: 0.69 },
          ];

    // Top jobs demo
    const topJobs = [
      { id: 1, title: 'Frontend Developer', applications: 48, avgScore: 79, applyRate: 0.14 },
      { id: 2, title: 'Backend Django', applications: 36, avgScore: 76, applyRate: 0.12 },
      { id: 3, title: 'QA Engineer', applications: 29, avgScore: 72, applyRate: 0.10 },
    ];

    const totals = baseSeries.reduce(
      (acc, s) => {
        acc.totalApplications += s.applications;
        acc.avgScoreSum += s.avgScore;
        acc.postEffectSum += s.postEffect;
        acc.shortlistedRateSum += s.shortlistedRate;
        acc.count += 1;
        return acc;
      },
      { totalApplications: 0, avgScoreSum: 0, postEffectSum: 0, shortlistedRateSum: 0, count: 0 }
    );

    return {
      summary: {
        totalApplications: totals.totalApplications,
        avgCandidateScore: Math.round(totals.avgScoreSum / totals.count),
        shortlistedRate: totals.shortlistedRateSum / totals.count,
        postEffectiveness: totals.postEffectSum / totals.count,
      },
      series: baseSeries,
      topJobs,
    };
  }, [period, year]);

  const [data, setData] = useState(mock);

  const fetchStats = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      // TODO: thay endpoint theo backend của bạn
      // const res = await Apis.get('/employer/stats', { params: { period, year } });
      // setData(res.data);

      // MVP: dùng mock
      setData(mock);
    } catch (e) {
      setError(e?.message || 'Load stats failed');
      setData(mock);
    } finally {
      setLoading(false);
    }
  }, [mock, period, year]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  return { data, loading, error, refetch: fetchStats };
}
