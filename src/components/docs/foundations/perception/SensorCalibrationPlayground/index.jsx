import React, { useMemo, useState } from 'react';
import Link from '@docusaurus/Link';
import {
  Armchair,
  Bot,
  CheckCircle2,
  Gauge,
  Home,
  MapPinned,
  Play,
  RefreshCw,
  Route,
  Settings,
  ShieldCheck,
  XCircle,
} from 'lucide-react';

const LEVELS = {
  easy: { label: 'Easy', trueYawDeg: 1.2, noiseCm: 1.0, frames: 30 },
  normal: { label: 'Normal', trueYawDeg: 1.8, noiseCm: 2.0, frames: 45 },
  hard: { label: 'Hard', trueYawDeg: 2.6, noiseCm: 4.0, frames: 60 },
};

const EMBODIMENTS = {
  arm: {
    label: '机械臂',
    subtitle: 'eye-in-hand grasp',
    metric: 'grasp_miss_m',
    scale: 0.55,
    thresholdM: 0.035,
    icon: Armchair,
  },
  mobile: {
    label: '移动机器人',
    subtitle: 'target approach',
    metric: 'nav_lateral_error_m',
    scale: 1.0,
    thresholdM: 0.12,
    icon: MapPinned,
  },
  quadruped: {
    label: '四足机器人',
    subtitle: 'target tracking',
    metric: 'tracking_or_foothold_error_m',
    scale: 0.75,
    thresholdM: 0.07,
    icon: Bot,
  },
};

const clamp = (value, lo, hi) => Math.max(lo, Math.min(hi, value));
const deg2rad = (value) => (value * Math.PI) / 180;
const rad2deg = (value) => (value * 180) / Math.PI;

function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a += 0x6d2b79f5;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function gaussian(rand) {
  const u = Math.max(rand(), 1e-9);
  const v = Math.max(rand(), 1e-9);
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

function simulate({ levelKey, embodimentKey, initialGuessDeg, updateGain, seed }) {
  const level = LEVELS[levelKey];
  const embodiment = EMBODIMENTS[embodimentKey];
  const rand = mulberry32(seed);
  let estimateDeg = initialGuessDeg;
  let residualWindow = [];
  const records = [];

  for (let idx = 0; idx < level.frames; idx += 1) {
    let distanceM = 2.0 + (idx % 9) * 0.75;
    if (idx % 13 === 0) distanceM = 1.5;

    const yawErrorRad = deg2rad(level.trueYawDeg - estimateDeg);
    const cleanResidualM = distanceM * Math.tan(yawErrorRad);
    const noiseM = gaussian(rand) * (level.noiseCm / 100.0);
    const residualM = cleanResidualM + noiseM;
    const yawMeasurementDeg = estimateDeg + rad2deg(Math.atan2(residualM, distanceM));

    residualWindow = [...residualWindow, Math.abs(residualM)].slice(-6);
    const meanAbsResidualM = residualWindow.reduce((sum, v) => sum + v, 0) / residualWindow.length;
    const triggered = distanceM >= 3.5 && meanAbsResidualM >= 0.05;

    if (triggered) {
      const step = updateGain * (yawMeasurementDeg - estimateDeg);
      estimateDeg += clamp(step, -0.35, 0.35);
    }

    const absErrorDeg = Math.abs(level.trueYawDeg - estimateDeg);
    const robotTaskErrorM = Math.abs(residualM) * embodiment.scale;
    const robotTaskSuccess = robotTaskErrorM < embodiment.thresholdM;
    const accepted = absErrorDeg < 0.2 && meanAbsResidualM < 0.045 && robotTaskSuccess;

    records.push({
      idx,
      distanceM,
      residualM,
      estimateDeg,
      absErrorDeg,
      meanAbsResidualM,
      robotTaskErrorM,
      robotTaskSuccess,
      triggered,
      accepted,
    });
  }

  const first = records[0];
  const last = records[records.length - 1];
  const finalWindow = records.slice(-6);
  const finalResidualM = finalWindow.reduce((sum, r) => sum + r.meanAbsResidualM, 0) / finalWindow.length;
  const finalTaskErrorM = finalWindow.reduce((sum, r) => sum + r.robotTaskErrorM, 0) / finalWindow.length;
  const taskSuccessRate = finalWindow.filter((r) => r.robotTaskSuccess).length / finalWindow.length;
  const residualImprovement = 1 - finalResidualM / Math.max(first.meanAbsResidualM, 1e-6);
  const convergenceFrame = records.find((r) => r.accepted)?.idx ?? -1;
  const passed = last.absErrorDeg < 0.25 && residualImprovement > 0.55 && convergenceFrame >= 0 && taskSuccessRate >= 0.75;

  return {
    records,
    summary: {
      trueYawDeg: level.trueYawDeg,
      finalEstimateDeg: last.estimateDeg,
      finalAbsErrorDeg: last.absErrorDeg,
      residualImprovement,
      convergenceFrame,
      finalTaskErrorM,
      taskSuccessRate,
      passed,
    },
  };
}

function MetricCard({ icon: Icon, label, value, tone = 'slate' }) {
  const color = {
    emerald: 'tw-border-emerald-700 tw-bg-emerald-950/50 tw-text-emerald-100',
    rose: 'tw-border-rose-700 tw-bg-rose-950/50 tw-text-rose-100',
    amber: 'tw-border-amber-700 tw-bg-amber-950/50 tw-text-amber-100',
    sky: 'tw-border-sky-700 tw-bg-sky-950/50 tw-text-sky-100',
    slate: 'tw-border-slate-700 tw-bg-slate-900/70 tw-text-slate-100',
  }[tone];
  return (
    <div className={`tw-rounded-lg tw-border tw-p-3 ${color}`}>
      <div className="tw-flex tw-items-center tw-gap-2 tw-text-xs tw-text-slate-300">
        <Icon size={14} />
        {label}
      </div>
      <div className="tw-mt-1 tw-text-xl tw-font-semibold">{value}</div>
    </div>
  );
}

function Slider({ label, value, min, max, step, onChange, suffix = '' }) {
  return (
    <label className="tw-block tw-rounded-lg tw-border tw-border-slate-700 tw-bg-slate-900/70 tw-p-3">
      <div className="tw-flex tw-items-center tw-justify-between tw-gap-3 tw-text-sm">
        <span className="tw-text-slate-200">{label}</span>
        <span className="tw-font-mono tw-text-sky-200">
          {Number(value).toFixed(step < 1 ? 2 : 0)}
          {suffix}
        </span>
      </div>
      <input
        className="tw-mt-3 tw-w-full"
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </label>
  );
}

function Chart({ records, embodiment }) {
  const w = 760;
  const h = 220;
  const pad = 28;
  const maxTask = Math.max(embodiment.thresholdM * 1.8, ...records.map((r) => r.robotTaskErrorM));
  const x = (idx) => pad + (idx / Math.max(records.length - 1, 1)) * (w - pad * 2);
  const yTask = (v) => h - pad - (v / maxTask) * (h - pad * 2);
  const yYaw = (v) => h - pad - (v / 3.2) * (h - pad * 2);
  const taskPath = records.map((r, i) => `${i === 0 ? 'M' : 'L'} ${x(i).toFixed(1)} ${yTask(r.robotTaskErrorM).toFixed(1)}`).join(' ');
  const yawPath = records.map((r, i) => `${i === 0 ? 'M' : 'L'} ${x(i).toFixed(1)} ${yYaw(r.estimateDeg).toFixed(1)}`).join(' ');
  const thresholdY = yTask(embodiment.thresholdM);
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="tw-h-full tw-w-full">
      <rect x="0" y="0" width={w} height={h} rx="12" fill="#020617" />
      <line x1={pad} x2={w - pad} y1={thresholdY} y2={thresholdY} stroke="#f59e0b" strokeDasharray="6 6" />
      <path d={taskPath} fill="none" stroke="#38bdf8" strokeWidth="3" />
      <path d={yawPath} fill="none" stroke="#a78bfa" strokeWidth="2" opacity="0.9" />
      {records.filter((r) => r.triggered).map((r) => (
        <circle key={`t-${r.idx}`} cx={x(r.idx)} cy={yTask(r.robotTaskErrorM)} r="3.2" fill="#22c55e" />
      ))}
      <text x={pad} y={18} fill="#cbd5e1" fontSize="12">task error</text>
      <text x={pad + 92} y={18} fill="#a78bfa" fontSize="12">yaw estimate</text>
      <text x={w - 150} y={thresholdY - 6} fill="#fbbf24" fontSize="12">task threshold</text>
    </svg>
  );
}

export default function SensorCalibrationPlayground() {
  const [levelKey, setLevelKey] = useState('normal');
  const [embodimentKey, setEmbodimentKey] = useState('arm');
  const [initialGuessDeg, setInitialGuessDeg] = useState(0);
  const [updateGain, setUpdateGain] = useState(0.35);
  const [seed, setSeed] = useState(7);

  const embodiment = EMBODIMENTS[embodimentKey];
  const { records, summary } = useMemo(
    () => simulate({ levelKey, embodimentKey, initialGuessDeg, updateGain, seed }),
    [levelKey, embodimentKey, initialGuessDeg, updateGain, seed],
  );
  const Icon = embodiment.icon;
  const sampled = records.filter((_, idx) => idx % Math.max(1, Math.floor(records.length / 12)) === 0).slice(0, 13);

  const reset = () => {
    setLevelKey('normal');
    setEmbodimentKey('arm');
    setInitialGuessDeg(0);
    setUpdateGain(0.35);
    setSeed(7);
  };

  return (
    <div className="tw-min-h-screen tw-bg-slate-950 tw-text-slate-100">
      <div className="tw-flex tw-items-center tw-justify-between tw-gap-3 tw-border-b tw-border-slate-800 tw-bg-slate-950/95 tw-px-4 tw-py-3">
        <Link to="/docs/foundations/perception/sensor-calibration-sim2real" className="tw-inline-flex tw-items-center tw-gap-2 tw-rounded-md tw-bg-slate-800 tw-px-3 tw-py-2 tw-text-sm tw-font-medium tw-text-slate-100 hover:tw-text-sky-200">
          <Home size={16} />
          返回章节
        </Link>
        <div className="tw-text-sm tw-font-semibold tw-text-slate-200">Sensor Calibration Playground</div>
        <button type="button" onClick={reset} className="tw-inline-flex tw-items-center tw-gap-2 tw-rounded-md tw-border tw-border-slate-700 tw-bg-slate-900 tw-px-3 tw-py-2 tw-text-sm tw-text-slate-100 hover:tw-border-sky-500">
          <RefreshCw size={16} />
          重置
        </button>
      </div>

      <main className="tw-grid tw-gap-4 tw-p-4 lg:tw-grid-cols-[360px_minmax(0,1fr)]">
        <section className="tw-space-y-4">
          <div className="tw-rounded-xl tw-border tw-border-slate-800 tw-bg-slate-900/80 tw-p-4">
            <div className="tw-flex tw-items-center tw-gap-3">
              <div className="tw-rounded-lg tw-bg-sky-500/10 tw-p-2 tw-text-sky-300">
                <Icon size={22} />
              </div>
              <div>
                <h1 className="tw-m-0 tw-text-lg tw-font-semibold">在线标定小游戏</h1>
                <p className="tw-m-0 tw-text-sm tw-text-slate-400">{embodiment.label} · {embodiment.subtitle}</p>
              </div>
            </div>
          </div>

          <div className="tw-rounded-xl tw-border tw-border-slate-800 tw-bg-slate-900/80 tw-p-4">
            <div className="tw-mb-3 tw-flex tw-items-center tw-gap-2 tw-text-sm tw-font-semibold">
              <Settings size={16} />
              任务与数据
            </div>
            <div className="tw-grid tw-grid-cols-3 tw-gap-2">
              {Object.entries(EMBODIMENTS).map(([key, item]) => {
                const ItemIcon = item.icon;
                const active = key === embodimentKey;
                return (
                  <button
                    key={key}
                    type="button"
                    onClick={() => setEmbodimentKey(key)}
                    className={`tw-rounded-lg tw-border tw-p-2 tw-text-left tw-transition ${active ? 'tw-border-sky-500 tw-bg-sky-950/70 tw-text-sky-100' : 'tw-border-slate-700 tw-bg-slate-950 tw-text-slate-300 hover:tw-border-slate-500'}`}
                  >
                    <ItemIcon size={16} />
                    <div className="tw-mt-1 tw-text-xs tw-font-medium">{item.label}</div>
                  </button>
                );
              })}
            </div>

            <div className="tw-mt-3 tw-grid tw-grid-cols-3 tw-gap-2">
              {Object.entries(LEVELS).map(([key, item]) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => setLevelKey(key)}
                  className={`tw-rounded-lg tw-border tw-px-3 tw-py-2 tw-text-sm tw-font-medium ${key === levelKey ? 'tw-border-emerald-500 tw-bg-emerald-950/70 tw-text-emerald-100' : 'tw-border-slate-700 tw-bg-slate-950 tw-text-slate-300 hover:tw-border-slate-500'}`}
                >
                  {item.label}
                </button>
              ))}
            </div>
          </div>

          <Slider label="初始 yaw 猜测" value={initialGuessDeg} min={-2} max={2} step={0.1} suffix=" deg" onChange={setInitialGuessDeg} />
          <Slider label="在线更新增益" value={updateGain} min={0.05} max={0.9} step={0.05} onChange={setUpdateGain} />
          <Slider label="随机种子" value={seed} min={1} max={30} step={1} onChange={setSeed} />

          <div className="tw-rounded-xl tw-border tw-border-slate-800 tw-bg-slate-900/80 tw-p-4">
            <div className="tw-flex tw-items-start tw-gap-2 tw-text-sm tw-text-slate-300">
              <Play className="tw-mt-0.5 tw-text-sky-300" size={16} />
              调滑块会立刻重跑仿真。绿色点表示触发在线更新；最后窗口任务成功率低于 75% 时验收失败。
            </div>
          </div>
        </section>

        <section className="tw-space-y-4">
          <div className="tw-grid tw-gap-3 md:tw-grid-cols-4">
            <MetricCard icon={Gauge} label="隐藏真实 yaw" value={`${summary.trueYawDeg.toFixed(2)} deg`} tone="sky" />
            <MetricCard icon={Route} label="最终任务误差" value={`${(summary.finalTaskErrorM * 100).toFixed(2)} cm`} tone={summary.passed ? 'emerald' : 'rose'} />
            <MetricCard icon={ShieldCheck} label="任务成功率" value={`${(summary.taskSuccessRate * 100).toFixed(1)}%`} tone={summary.passed ? 'emerald' : 'amber'} />
            <MetricCard icon={summary.passed ? CheckCircle2 : XCircle} label="工程验收" value={summary.passed ? 'PASS' : 'FAIL'} tone={summary.passed ? 'emerald' : 'rose'} />
          </div>

          <div className="tw-rounded-xl tw-border tw-border-slate-800 tw-bg-slate-900/80 tw-p-4">
            <div className="tw-mb-3 tw-flex tw-items-center tw-justify-between tw-gap-2">
              <div className="tw-text-sm tw-font-semibold tw-text-slate-200">任务误差与外参估计</div>
              <div className="tw-text-xs tw-text-slate-400">{embodiment.metric} &lt; {(embodiment.thresholdM * 100).toFixed(1)} cm</div>
            </div>
            <div className="tw-aspect-[16/5] tw-min-h-[220px]">
              <Chart records={records} embodiment={embodiment} />
            </div>
          </div>

          <div className="tw-grid tw-gap-4 xl:tw-grid-cols-[1fr_320px]">
            <div className="tw-overflow-hidden tw-rounded-xl tw-border tw-border-slate-800 tw-bg-slate-900/80">
              <div className="tw-border-b tw-border-slate-800 tw-px-4 tw-py-3 tw-text-sm tw-font-semibold">采样帧</div>
              <div className="tw-overflow-x-auto">
                <table className="tw-w-full tw-min-w-[680px] tw-text-left tw-text-sm">
                  <thead className="tw-bg-slate-950/80 tw-text-xs tw-text-slate-400">
                    <tr>
                      <th className="tw-px-3 tw-py-2">frame</th>
                      <th className="tw-px-3 tw-py-2">distance</th>
                      <th className="tw-px-3 tw-py-2">residual</th>
                      <th className="tw-px-3 tw-py-2">estimate</th>
                      <th className="tw-px-3 tw-py-2">task error</th>
                      <th className="tw-px-3 tw-py-2">event</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sampled.map((r) => (
                      <tr key={r.idx} className="tw-border-t tw-border-slate-800">
                        <td className="tw-px-3 tw-py-2 tw-font-mono">{r.idx}</td>
                        <td className="tw-px-3 tw-py-2">{r.distanceM.toFixed(2)} m</td>
                        <td className="tw-px-3 tw-py-2">{(r.residualM * 100).toFixed(2)} cm</td>
                        <td className="tw-px-3 tw-py-2">{r.estimateDeg.toFixed(3)} deg</td>
                        <td className="tw-px-3 tw-py-2">{(r.robotTaskErrorM * 100).toFixed(2)} cm</td>
                        <td className="tw-px-3 tw-py-2">
                          <span className={`tw-rounded tw-px-2 tw-py-1 tw-text-xs ${r.accepted ? 'tw-bg-emerald-900 tw-text-emerald-100' : r.triggered ? 'tw-bg-sky-900 tw-text-sky-100' : 'tw-bg-slate-800 tw-text-slate-300'}`}>
                            {r.accepted ? 'ACCEPT' : r.triggered ? 'UPDATE' : 'watch'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="tw-rounded-xl tw-border tw-border-slate-800 tw-bg-slate-900/80 tw-p-4">
              <div className="tw-text-sm tw-font-semibold tw-text-slate-200">验收规则</div>
              <ul className="tw-mt-3 tw-space-y-2 tw-pl-0 tw-text-sm tw-text-slate-300">
                <li className="tw-list-none">final yaw error &lt; 0.25 deg</li>
                <li className="tw-list-none">residual improvement &gt; 55%</li>
                <li className="tw-list-none">出现 accepted frame</li>
                <li className="tw-list-none">final task success rate &gt;= 75%</li>
              </ul>
              <div className="tw-mt-4 tw-rounded-lg tw-bg-slate-950 tw-p-3 tw-font-mono tw-text-xs tw-text-slate-300">
                final_estimate={summary.finalEstimateDeg.toFixed(3)} deg<br />
                residual_improve={(summary.residualImprovement * 100).toFixed(1)}%<br />
                convergence_frame={summary.convergenceFrame}
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
