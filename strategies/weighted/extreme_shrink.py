# strategies/weighted/extreme_shrink.py
import pandas as pd
import numpy as np
from ...strategies.registry import register_strategy

class WeightedScoringStrategy:
    def __init__(self, params: dict = None):
        default = {
            'min_score': 60,
            'vol_ratio_threshold': 0.8,
            'vol_score_levels': {0.5: 40, 0.6: 38, 0.7: 35, 0.8: 30},
            'drop_small': (-2, 0, 10),
            'drop_medium': (-4, -2, 8),
            'drop_large': (-100, -4, 5),
            'trend_far_below': 10,
            'trend_below': 5,
            'trend_above': 10,
            'volatility_low': 3.0,
            'volatility_mid': 4.5,
            'price_low_max': 30,
            'price_mid_max': 80,
            'extra_body_small': 1.0,
            'extra_lower_shadow': 1.5,
            'extra_vol_ratio': 0.6,
        }
        self.params = default
        if params:
            self.params.update(params)

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['volume'] = df.get('vol', df['volume'])
        df = df.sort_values(['ts_code', 'trade_date'])

        df['ma_60'] = df.groupby('ts_code')['close'].transform(lambda x: x.rolling(60).mean())
        df['vol_ma20'] = df.groupby('ts_code')['volume'].transform(lambda x: x.rolling(20).mean())
        df['prev_vol_min_20'] = df.groupby('ts_code')['volume'].transform(lambda x: x.shift(1).rolling(20).min())
        df['amplitude'] = (df['high'] - df['low']) / df['low'] * 100
        df['amp_ma15'] = df.groupby('ts_code')['amplitude'].transform(lambda x: x.rolling(15).mean())
        df['pct_change'] = df.groupby('ts_code')['close'].transform(lambda x: x.pct_change() * 100)
        df['distance_ma60'] = (df['close'] - df['ma_60']) / df['ma_60'] * 100
        df['vol_ratio'] = df['volume'] / df['vol_ma20']
        return df

    def calculate_scores(self, row: pd.Series) -> dict:
        p = self.params
        scores = {'总分': 0}

        if row['close'] >= row['open']:
            scores['淘汰原因'] = '非绿盘'
            return scores
        if pd.isnull(row['prev_vol_min_20']) or row['volume'] >= row['prev_vol_min_20'] * p['vol_ratio_threshold']:
            scores['淘汰原因'] = '未极致缩量'
            return scores

        ratio = row['volume'] / row['prev_vol_min_20']
        vol_score = 30
        for th, sc in sorted(p['vol_score_levels'].items(), reverse=True):
            if ratio <= th:
                vol_score = sc
                break

        pct = row['pct_change']
        if p['drop_small'][0] <= pct < p['drop_small'][1]:
            drop_score = p['drop_small'][2]
        elif p['drop_medium'][0] <= pct < p['drop_medium'][1]:
            drop_score = p['drop_medium'][2]
        else:
            drop_score = p['drop_large'][2]

        dist = row['distance_ma60'] if pd.notnull(row['distance_ma60']) else 0
        if dist < 0:
            abs_dist = abs(dist)
            trend_score = 15 if abs_dist >= p['trend_far_below'] else 12 if abs_dist >= p['trend_below'] else 8
        else:
            trend_score = p['trend_above']

        amp = row['amp_ma15'] if pd.notnull(row['amp_ma15']) else 999
        volatility_score = 10 if amp < p['volatility_low'] else 6 if amp < p['volatility_mid'] else 3

        price = row['close']
        price_score = 10 if price <= p['price_low_max'] else 5 if price <= p['price_mid_max'] else 0

        extra = 0
        if abs(row['close'] - row['open']) / row['open'] * 100 < p['extra_body_small']:
            extra += 5
        if (min(row['open'], row['close']) - row['low']) / row['low'] * 100 > p['extra_lower_shadow']:
            extra += 5
        if row['vol_ratio'] < p['extra_vol_ratio']:
            extra += 5
        extra = min(15, extra)

        total = vol_score + drop_score + trend_score + volatility_score + price_score + extra
        scores['总分'] = min(100, total)
        scores['_ratio'] = ratio
        scores['_pct'] = pct
        return scores

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame()
        df = self.calculate_indicators(df)
        current = df[df['trade_date'] == df['trade_date'].max()]
        results = []
        for _, row in current.iterrows():
            scores = self.calculate_scores(row)
            if scores['总分'] >= self.params['min_score']:
                res = row.to_dict()
                res.update(scores)
                results.append(res)
        if not results:
            return pd.DataFrame()
        final = pd.DataFrame(results).sort_values('总分', ascending=False)
        final['reason'] = final.apply(lambda x: f"极致缩量{x['总分']}分|前低{x['_ratio']:.2f}倍|跌{x['_pct']:.1f}%", axis=1)
        return final

# 注册策略
@register_strategy(name="加权评分-极致缩量（标准）", default_params={'min_score': 60, 'vol_ratio_threshold': 0.8})
def run_standard(df, params=None):
    strategy_params = {'min_score': 60, 'vol_ratio_threshold': 0.8}
    if params:
        strategy_params.update(params)
    return WeightedScoringStrategy(strategy_params).run(df)

@register_strategy(name="加权评分-极致缩量（宽松）", default_params={'min_score': 50, 'vol_ratio_threshold': 0.9})
def run_relaxed(df, params=None):
    strategy_params = {'min_score': 50, 'vol_ratio_threshold': 0.9}
    if params:
        strategy_params.update(params)
    return WeightedScoringStrategy(strategy_params).run(df)
