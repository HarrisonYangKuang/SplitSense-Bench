# 时间验证机制核查：不能把时间索引本身作为错误标签

2026-09-08；rapid-scan（快速定向检索），不是系统综述或新颖性结论。用途：检验“随机验证在时间任务上必然错误”的前提，指导下一次任务设计。没有启动新实验。

## 核实来源

Bergmeir, Hyndman, Koo (2018), *A note on the validity of cross-validation for evaluating autoregressive time series prediction*, Computational Statistics & Data Analysis 120:70–83，[正式出版 DOI](https://doi.org/10.1016/j.csda.2017.11.003)。详细核查使用[作者提供的 2017-07-23 预印本](https://robjhyndman.com/papers/cv-wp.pdf)，不假定它与出版排版逐字相同。

该文不是对所有时间任务允许随机划分的证明。第 3 节明确包含平稳、遍历自回归过程、一致估计及误差条件；其定理的适用性不能由“包含滞后特征”直接推出。第 4 节研究单步预测，并在模型选择后用完整内部数据重新拟合。季节性反例中，候选只使用较短滞后，未覆盖生成机制的季节性滞后。

## 对本项目的影响：推论，而非复现结果

1. v38 使用延迟目标特征，但尚未证明满足该文假设，且并非同一标准单步设定。论文不能替 v38 宣布随机验证有效，也不能替时间验证宣告无效。
2. 文献反例提醒我们检查候选表示是否遗漏关键依赖；但为了获得正结果而删除合法季节性候选，会重演原四任务的候选集合问题。保留强候选的要求不变。
3. 因此下一次时间任务应在训练前说清具体失配机制、部署信息集和可见识别依据。只更换时间序列、发现自相关、或把残差检验未拒绝当作假设已成立，都不足以支持新一轮训练。
4. Skill 应允许条件化判断，而非教 Agent 看到日期就选时间划分。已对清单第 8 项作开发版修订；尚无干预效果证据。旧版本仍由 Git 历史保留，历史结果不重新归属。

## 检索记录与限制

查询一：`Bergmeir Hyndman Koo 2018 validity cross validation evaluating autoregressive time series prediction uncorrelated errors`。
查询二：`Roberts cross validation strategies temporal hierarchical spatial structured data 2017 extrapolation prediction`。
渠道：网页搜索、作者页面及作者 PDF；核实一个直接相关研究。Roberts 等人的结构化验证论文检索到但本次未完成正文提取，不据此作技术结论。没有独立筛选、引文链穷尽或完整新颖性检查。

本次行动是修正研究前提和未验证的 Skill 草稿，不是通过 task validity gate。原有失败结果、门槛、公开版本和正式 Agent 评测限制全部保留。
