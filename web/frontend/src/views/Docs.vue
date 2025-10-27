<template>
  <div class="docs">
    <el-card class="header-card" shadow="never">
      <div class="page-header">
        <h1>📚 使用文档</h1>
      </div>
    </el-card>

    <!-- 快速开始 -->
    <el-card class="doc-section" shadow="hover">
      <template #header>
        <span class="section-title">
          <el-icon><Promotion /></el-icon>
          快速开始
        </span>
      </template>

      <el-alert
        title="欢迎使用金融工具平台！"
        type="success"
        :closable="false"
        show-icon
      >
        <p>本平台提供美股市场分析、VIX恐慌指数监控、行业轮动分析、策略回测等功能。</p>
      </el-alert>

      <el-divider />

      <h3>🎯 核心功能</h3>
      <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="6">
          <el-card shadow="hover" class="feature-card">
            <template #header>
              <el-icon><TrendCharts /></el-icon>
              指数分析
            </template>
            <p>基于历史点位相似度分析，预测未来走势概率</p>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="feature-card">
            <template #header>
              <el-icon><Orange /></el-icon>
              VIX恐慌指数
            </template>
            <p>实时监控市场恐慌情绪，把握市场风险信号</p>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="feature-card">
            <template #header>
              <el-icon><Refresh /></el-icon>
              行业轮动
            </template>
            <p>追踪11个行业ETF表现，识别行业轮动机会</p>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="feature-card">
            <template #header>
              <el-icon><DataAnalysis /></el-icon>
              历史回测
            </template>
            <p>验证四指标共振策略的历史表现和收益</p>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <!-- 指数分析使用指南 -->
    <el-card class="doc-section" shadow="hover">
      <template #header>
        <span class="section-title">
          <el-icon><TrendCharts /></el-icon>
          指数分析使用指南
        </span>
      </template>

      <h3>📊 功能说明</h3>
      <p>通过查找历史上相似点位，统计后续涨跌情况，预测当前点位的未来走势概率。</p>

      <h3>🔧 使用步骤</h3>
      <el-steps direction="vertical" :active="4">
        <el-step title="选择指数" description="选择要分析的美股指数（标普500/纳斯达克/纳斯达克100等）" />
        <el-step title="配置参数" description="设置相似度容差（建议3-10%）和分析周期（5/10/20/60日）" />
        <el-step title="运行分析" description="点击开始分析按钮，系统将查找历史相似点位" />
        <el-step title="查看结果" description="查看涨跌概率、平均收益率、置信度和仓位建议" />
      </el-steps>

      <el-divider />

      <h3>📈 结果解读</h3>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="上涨概率">
          基于历史相似点位后续上涨的比例计算，>65%可考虑买入
        </el-descriptions-item>
        <el-descriptions-item label="平均收益率">
          历史相似点位后续的平均涨跌幅，正值表示平均上涨
        </el-descriptions-item>
        <el-descriptions-item label="置信度">
          基于样本量和结果一致性计算，>70%置信度较高
        </el-descriptions-item>
        <el-descriptions-item label="建议仓位">
          综合概率、收益率和置信度计算的推荐仓位比例
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <!-- VIX指数使用指南 -->
    <el-card class="doc-section" shadow="hover">
      <template #header>
        <span class="section-title">
          <el-icon><Orange /></el-icon>
          VIX恐慌指数使用指南
        </span>
      </template>

      <h3>🔥 VIX是什么？</h3>
      <p>
        VIX（波动率指数）被称为"恐慌指数"，反映市场对未来30天波动性的预期。
        VIX越高，市场恐慌程度越高；VIX越低，市场越平静。
      </p>

      <h3>📊 VIX解读</h3>
      <el-table :data="vixLevels" border style="margin-top: 15px">
        <el-table-column prop="range" label="VIX范围" width="120" />
        <el-table-column prop="level" label="恐慌等级" width="120" />
        <el-table-column prop="meaning" label="市场含义" />
        <el-table-column prop="strategy" label="操作建议" />
      </el-table>

      <el-divider />

      <h3>💡 使用技巧</h3>
      <ul>
        <li><strong>VIX飙升（>30）：</strong>市场极度恐慌，往往是买入机会（抄底）</li>
        <li><strong>VIX极低（&lt;15）：</strong>市场过于乐观，需警惕风险（减仓）</li>
        <li><strong>VIX急速上升：</strong>短期内快速上涨>20%，表明市场不确定性增加</li>
        <li><strong>VIX分位数：</strong>查看当前VIX在历史中的位置，判断是高位还是低位</li>
      </ul>
    </el-card>

    <!-- 行业轮动使用指南 -->
    <el-card class="doc-section" shadow="hover">
      <template #header>
        <span class="section-title">
          <el-icon><Refresh /></el-icon>
          行业轮动使用指南
        </span>
      </template>

      <h3>🔄 行业轮动原理</h3>
      <p>
        不同经济周期下，不同行业表现各异。通过追踪11个行业ETF的相对强度，
        识别当前市场处于哪个阶段，以及哪些行业更具投资价值。
      </p>

      <h3>📊 市场轮动模式</h3>
      <el-descriptions :column="1" border style="margin-top: 15px">
        <el-descriptions-item label="进攻型轮动">
          科技、可选消费、通讯等成长型行业领涨，市场风险偏好高
        </el-descriptions-item>
        <el-descriptions-item label="防守型轮动">
          公用事业、必需消费、医疗等防御型行业领涨，市场避险情绪浓
        </el-descriptions-item>
        <el-descriptions-item label="周期型轮动">
          能源、材料、工业等周期性行业领涨，经济复苏阶段
        </el-descriptions-item>
      </el-descriptions>

      <el-divider />

      <h3>💼 11个行业ETF</h3>
      <el-row :gutter="15" style="margin-top: 15px">
        <el-col :span="6" v-for="sector in sectors" :key="sector.code">
          <el-tag size="large" style="width: 100%; margin-bottom: 10px">
            <strong>{{ sector.code }}</strong> - {{ sector.name }}
          </el-tag>
        </el-col>
      </el-row>
    </el-card>

    <!-- 历史回测使用指南 -->
    <el-card class="doc-section" shadow="hover">
      <template #header>
        <span class="section-title">
          <el-icon><DataAnalysis /></el-icon>
          历史回测使用指南
        </span>
      </template>

      <h3>🎯 策略说明</h3>
      <p>
        <strong>四指标共振策略：</strong>综合趋势指标、动量指标、超买超卖指标和成交量指标，
        当多个指标同时发出买入/卖出信号时，进行交易操作。
      </p>

      <h3>📝 参数配置</h3>
      <el-descriptions :column="2" border style="margin-top: 15px">
        <el-descriptions-item label="回测标的">
          支持美股指数和ETF（如SPX、SPY、QQQ等）
        </el-descriptions-item>
        <el-descriptions-item label="回测天数">
          建议500-1000天，数据越多越能反映策略稳定性
        </el-descriptions-item>
        <el-descriptions-item label="初始资金">
          回测起始资金，建议10万以上
        </el-descriptions-item>
        <el-descriptions-item label="手续费率">
          固定0.03%（双向收取）
        </el-descriptions-item>
        <el-descriptions-item label="止损比例">
          建议5-10%，控制单笔交易最大亏损
        </el-descriptions-item>
        <el-descriptions-item label="止盈比例">
          建议10-20%，及时锁定利润
        </el-descriptions-item>
      </el-descriptions>

      <el-divider />

      <h3>📊 性能指标解读</h3>
      <ul>
        <li><strong>总收益率/年化收益率：</strong>策略的收益表现，年化收益>15%为优秀</li>
        <li><strong>最大回撤：</strong>策略最大损失幅度，<20%为可接受</li>
        <li><strong>夏普比率：</strong>风险调整后收益，>1为优秀，>2为非常优秀</li>
        <li><strong>胜率：</strong>盈利交易占比，>50%为正向策略</li>
        <li><strong>盈亏比：</strong>平均盈利/平均亏损比例，>1.5为较好</li>
      </ul>
    </el-card>

    <!-- 常见问题 -->
    <el-card class="doc-section" shadow="hover">
      <template #header>
        <span class="section-title">
          <el-icon><QuestionFilled /></el-icon>
          常见问题
        </span>
      </template>

      <el-collapse>
        <el-collapse-item title="Q1: 数据来源是什么？" name="1">
          <p>
            本平台使用yfinance作为数据源，获取Yahoo Finance的实时和历史行情数据。
            数据质量可靠，覆盖全球主要市场。
          </p>
        </el-collapse-item>

        <el-collapse-item title="Q2: 指数分析的准确率如何？" name="2">
          <p>
            指数分析基于历史相似度统计，<strong>不是预测未来，而是提供概率参考</strong>。
            置信度>70%的结果相对可靠，但历史不代表未来，需结合其他分析方法。
          </p>
        </el-collapse-item>

        <el-collapse-item title="Q3: VIX指数如何使用？" name="3">
          <p>
            VIX是反向指标：VIX高时（>30），市场恐慌，往往是买入机会；
            VIX低时（<15），市场乐观，需警惕风险。
            但VIX只是辅助指标，不能单独作为交易依据。
          </p>
        </el-collapse-item>

        <el-collapse-item title="Q4: 回测结果能直接用于实盘吗？" name="4">
          <p>
            <strong>不建议直接用于实盘。</strong>回测存在过拟合风险，历史表现不代表未来收益。
            回测结果仅供参考，实盘需要充分理解策略逻辑，并做好风险管理。
          </p>
        </el-collapse-item>

        <el-collapse-item title="Q5: 支持哪些市场？" name="5">
          <p>
            当前版本支持<strong>美股市场</strong>（指数、ETF）。
            未来计划支持港股和A股市场，敬请期待。
          </p>
        </el-collapse-item>

        <el-collapse-item title="Q6: 如何联系技术支持？" name="6">
          <p>
            如有问题或建议，请访问项目GitHub仓库提交Issue：
            <el-link type="primary" href="https://github.com/your-repo" target="_blank">
              GitHub Repository
            </el-link>
          </p>
        </el-collapse-item>
      </el-collapse>
    </el-card>

    <!-- 免责声明 -->
    <el-card class="doc-section" shadow="hover">
      <template #header>
        <span class="section-title">
          <el-icon><WarningFilled /></el-icon>
          免责声明
        </span>
      </template>

      <el-alert
        title="重要提示"
        type="warning"
        :closable="false"
        show-icon
      >
        <ul style="margin: 0; padding-left: 20px">
          <li>本平台仅供学习和研究使用，<strong>不构成投资建议</strong></li>
          <li>所有分析结果基于历史数据，<strong>不保证未来收益</strong></li>
          <li>投资有风险，入市需谨慎，<strong>请独立思考和决策</strong></li>
          <li>使用本平台产生的任何投资损失，<strong>平台不承担责任</strong></li>
        </ul>
      </el-alert>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// VIX等级数据
const vixLevels = ref([
  {
    range: '< 15',
    level: '过度乐观',
    meaning: '市场过于平静，波动性极低',
    strategy: '警惕风险，考虑减仓或对冲',
  },
  {
    range: '15 - 20',
    level: '正常区间',
    meaning: '市场情绪平稳，波动性正常',
    strategy: '正常操作，保持观察',
  },
  {
    range: '20 - 30',
    level: '恐慌上升',
    meaning: '市场担忧情绪较高，波动增加',
    strategy: '谨慎操作，可逢低布局',
  },
  {
    range: '> 30',
    level: '极度恐慌',
    meaning: '市场极度恐慌，历史少见',
    strategy: '往往是买入机会（抄底）',
  },
])

// 11个行业ETF
const sectors = ref([
  { code: 'XLK', name: '科技' },
  { code: 'XLF', name: '金融' },
  { code: 'XLE', name: '能源' },
  { code: 'XLV', name: '医疗' },
  { code: 'XLI', name: '工业' },
  { code: 'XLP', name: '必需消费' },
  { code: 'XLY', name: '可选消费' },
  { code: 'XLB', name: '材料' },
  { code: 'XLRE', name: '房地产' },
  { code: 'XLU', name: '公用事业' },
  { code: 'XLC', name: '通讯服务' },
])
</script>

<style scoped>
.docs {
  width: 100%;
}

.header-card {
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
}

.doc-section {
  margin-bottom: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.feature-card {
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.feature-card :deep(.el-card__header) {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
}

.feature-card p {
  color: #606266;
  font-size: 14px;
  margin: 0;
}

h3 {
  color: #303133;
  margin-top: 20px;
  margin-bottom: 15px;
}

p, li {
  line-height: 1.8;
  color: #606266;
}

ul {
  padding-left: 25px;
}

ul li {
  margin-bottom: 10px;
}

:deep(.el-descriptions__label) {
  font-weight: 600;
}

:deep(.el-collapse-item__header) {
  font-weight: 600;
  font-size: 15px;
}

/* 动画效果 */
@keyframes fade-up {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.doc-section {
  animation: fade-up 0.6s ease-out backwards;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.doc-section:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.12);
}

.doc-section:nth-child(1) {
  animation-delay: 0.1s;
}

.doc-section:nth-child(2) {
  animation-delay: 0.2s;
}

.doc-section:nth-child(3) {
  animation-delay: 0.3s;
}

.doc-section:nth-child(4) {
  animation-delay: 0.4s;
}

.doc-section:nth-child(5) {
  animation-delay: 0.5s;
}

.doc-section:nth-child(6) {
  animation-delay: 0.6s;
}

.doc-section:nth-child(7) {
  animation-delay: 0.7s;
}

.feature-card {
  animation: fade-up 0.5s ease-out backwards;
}

@media (max-width: 768px) {
  .page-header h1 {
    font-size: 20px;
  }

  .section-title {
    font-size: 14px;
  }

  .feature-card :deep(.el-card__header) {
    font-size: 14px;
  }

  .feature-card p {
    font-size: 13px;
  }

  h3 {
    font-size: 16px;
  }

  p, li {
    font-size: 14px;
  }

  .el-descriptions,
  .el-table {
    font-size: 13px;
  }

  .el-collapse-item__header {
    font-size: 14px;
  }

  :deep(.el-row .el-col) {
    margin-bottom: 10px;
  }
}
</style>
