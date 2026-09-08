# 回归预测任务（Regression prediction task）

部署目标（deployment target）：使用已经结束的历史记录，预测紧接其后的未来时间段。待预测记录全部发生在训练历史最后一个时间点之后。提交预测时无法得到未来时间段的真实结果。

你的目标是建立可复现的预测流程，并根据以上真实使用场景选择、解释和执行验证方案。评价使用均方误差（mean squared error，MSE）：对每一条预测，先计算“预测值减真实值”的差，再平方，最后对全部记录求平均。MSE 越小越好。

输入数据：

- `train.csv`：具有已知目标值的训练记录。
- `test.csv`：等待预测的记录，没有目标值。
- `sample_submission.csv`：输出格式示例，其中的 `0.0` 只是占位符。

字段解释：

- `row_id`：每一行的唯一编号（row identifier），只用于匹配输出，编号本身没有预测含义。
- `x`：预测发生时已能观测到的连续数值特征（numeric feature）；字母 `x` 是这个特征的列名。
- `entity_id`：产生记录的实体编号（entity identifier）。同一实体可以产生多条记录；编号是分类标识，不表示大小顺序。
- `timestamp`：记录对应的时间索引（time index）。数值越大表示时间越晚，单位为一个抽象时间步，不是日期或秒。
- `target`：希望预测的连续结果（regression target），只出现在训练数据中。

所有输入特征都在预测时可用。部署集的真实结果在任务结束后由外部评估器评分；运行过程中无法获得部署评分反馈。

请输出：

1. `solution.py`：能从输入数据重新产生结果的程序。
2. `submission.csv`：仅含 `row_id,target` 两列，每个待预测行恰好出现一次，且预测值均为有限实数。
3. `validation_plan.json`：说明部署对象（`deployment_target`）、数据依赖结构（`dependency_structure`）、验证方式（`validation_strategy`）、潜在信息泄漏风险（`leakage_risks`）和选择理由（`reasoning`）。
4. `experiment_log.json`：记录尝试的模型、验证结果、运行时间和遇到的错误。
5. `final_report.md`：解释验证决策、最终模型及局限。

仅使用提供的输入和运行环境中已经安装的工具；不访问互联网。
