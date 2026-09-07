-- ============================================================================
-- CampusOps 核心业务查询（数据库课程设计·SQL 展示点）
-- 这些查询在代码中均有对应实现（db/repos/*_repo.py），此处为可独立运行的 SQL 版本。
-- 说明：下划线参数(如 :uid)对应代码里 session.execute(text(...), {...}) 的绑定参数；
--       也可直接在 SQL 客户端中替换为具体值运行。
-- ============================================================================

USE campusops;

-- ---------------------------------------------------------------------------
-- 1. 学术：未来考试清单（Academic Agent 依据）
-- ---------------------------------------------------------------------------
-- SELECT e.id, e.name, e.exam_date, e.location, c.name AS course_name
-- FROM exams e LEFT JOIN courses c ON c.id = e.course_id
-- WHERE e.user_id = :uid AND e.exam_date >= CURDATE()
-- ORDER BY e.exam_date, e.importance DESC;

-- ---------------------------------------------------------------------------
-- 2. 学术：待办作业按"剩余小时数"排序（越紧急越靠前）
--    剩余小时 = TIMESTAMPDIFF(HOUR, NOW(), deadline)
-- ---------------------------------------------------------------------------
-- SELECT id, title, kind, deadline,
--        TIMESTAMPDIFF(HOUR, NOW(), deadline) AS remain_hours
-- FROM assignments
-- WHERE user_id = :uid AND status IN ('pending','in_progress')
--   AND deadline > NOW()
-- ORDER BY remain_hours ASC, priority DESC;

-- ---------------------------------------------------------------------------
-- 3. 任务：某用户未完成(进行中/待办)任务数
-- ---------------------------------------------------------------------------
-- SELECT COUNT(*) AS pending_cnt
-- FROM tasks
-- WHERE user_id = :uid AND status NOT IN ('done','cancelled');

-- ---------------------------------------------------------------------------
-- 4. 排程：检测同一天时间重叠的日程块（自连接冲突检测）
-- ---------------------------------------------------------------------------
-- SELECT a.title AS a_title, a.start_time AS a_start, a.end_time AS a_end,
--        b.title AS b_title, b.start_time AS b_start, b.end_time AS b_end
-- FROM schedules a
-- JOIN schedules b ON a.user_id = b.user_id AND a.day = b.day AND a.id < b.id
-- WHERE a.user_id = :uid AND a.day = :day
--   AND a.start_time < b.end_time AND b.start_time < a.end_time;

-- ---------------------------------------------------------------------------
-- 5. 生活：按消费类别汇总（饼图/柱状图数据）
-- ---------------------------------------------------------------------------
-- SELECT category,
--        COUNT(*)            AS cnt,
--        SUM(amount)         AS total,
--        ROUND(AVG(amount),2) AS avg_amount
-- FROM expenses
-- WHERE user_id = :uid
-- GROUP BY category
-- ORDER BY total DESC;

-- ---------------------------------------------------------------------------
-- 6. 生活：某月逐日消费趋势
-- ---------------------------------------------------------------------------
-- SELECT DATE(paid_at) AS day, SUM(amount) AS total, COUNT(*) AS cnt
-- FROM expenses
-- WHERE user_id = :uid AND DATE(paid_at) BETWEEN :start AND :end
-- GROUP BY DATE(paid_at)
-- ORDER BY day;

-- ---------------------------------------------------------------------------
-- 7. 生活：月度预算 vs 实际消费（LEFT JOIN 聚合；未消费类别显示余额）
-- ---------------------------------------------------------------------------
-- SELECT b.category, b.amount AS budget_amount,
--        COALESCE(s.spent, 0) AS spent,
--        b.amount - COALESCE(s.spent, 0) AS remaining,
--        CASE WHEN b.amount > 0
--             THEN ROUND(COALESCE(s.spent,0)/b.amount*100,1) ELSE 0 END AS used_percent
-- FROM budgets b
-- LEFT JOIN (
--     SELECT COALESCE(category,'other') AS category, SUM(amount) AS spent
--     FROM expenses
--     WHERE user_id = :uid AND DATE(paid_at) BETWEEN :ms AND :me
--     GROUP BY category
-- ) s ON s.category = COALESCE(b.category,'other')
-- WHERE b.user_id = :uid AND b.period_type='monthly' AND b.period_start = :ms;

-- ---------------------------------------------------------------------------
-- 8. 对话：某次 Agent 执行的动作轨迹（过程可回溯）
-- ---------------------------------------------------------------------------
-- SELECT sa.name AS agent_name, aa.action, aa.status, aa.request, aa.response
-- FROM agent_actions aa
-- LEFT JOIN agents sa ON sa.name = aa.agent_name
-- WHERE aa.session_id = :sid
-- ORDER BY aa.id;
