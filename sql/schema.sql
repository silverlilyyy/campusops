-- CampusOps 数据库结构（由 db/models 自动导出）
-- 说明：仅供查阅与文档使用；建库请运行 python scripts/init_db.py

CREATE DATABASE IF NOT EXISTS campusops DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE campusops;


CREATE TABLE agents (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	name VARCHAR(32) NOT NULL COMMENT 'manager/academic/schedule/finance', 
	display_name VARCHAR(64) COMMENT '展示名', 
	description TEXT COMMENT '职责描述', 
	enabled BOOL COMMENT '是否启用', 
	created_at DATETIME NOT NULL COMMENT '创建时间' DEFAULT now(), 
	updated_at DATETIME NOT NULL COMMENT '更新时间' DEFAULT now(), 
	PRIMARY KEY (id), 
	UNIQUE (name)
)COMMENT='Agent注册表'




CREATE TABLE users (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	username VARCHAR(64) NOT NULL COMMENT '登录名', 
	password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希', 
	nickname VARCHAR(64) COMMENT '昵称', 
	email VARCHAR(128) COMMENT '邮箱', 
	avatar_url VARCHAR(255) COMMENT '头像地址', 
	created_at DATETIME NOT NULL COMMENT '创建时间' DEFAULT now(), 
	updated_at DATETIME NOT NULL COMMENT '更新时间' DEFAULT now(), 
	PRIMARY KEY (id), 
	UNIQUE (username)
)COMMENT='用户'




CREATE TABLE activities (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	user_id BIGINT NOT NULL COMMENT '所属用户', 
	name VARCHAR(128) NOT NULL COMMENT '活动名称', 
	category VARCHAR(32) COMMENT '活动类型，如 社团/讲座/团建', 
	start_time DATETIME NOT NULL COMMENT '开始时间', 
	end_time DATETIME COMMENT '结束时间', 
	location VARCHAR(128) COMMENT '地点', 
	importance SMALLINT COMMENT '重要度1-5', 
	note TEXT COMMENT '备注', 
	created_at DATETIME NOT NULL COMMENT '创建时间' DEFAULT now(), 
	updated_at DATETIME NOT NULL COMMENT '更新时间' DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)COMMENT='活动'




CREATE TABLE budgets (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	user_id BIGINT NOT NULL COMMENT '所属用户', 
	period_type VARCHAR(16) NOT NULL COMMENT 'daily/weekly/monthly', 
	period_start DATE NOT NULL COMMENT '周期开始', 
	period_end DATE NOT NULL COMMENT '周期结束', 
	category VARCHAR(32) COMMENT '类别预算，空=总预算', 
	amount DECIMAL(10, 2) NOT NULL COMMENT '预算金额', 
	created_at DATETIME NOT NULL COMMENT '创建时间' DEFAULT now(), 
	updated_at DATETIME NOT NULL COMMENT '更新时间' DEFAULT now(), 
	PRIMARY KEY (id), 
	CONSTRAINT uk_budget UNIQUE (user_id, period_type, period_start, category), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)COMMENT='预算'




CREATE TABLE conversations (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	user_id BIGINT NOT NULL COMMENT '所属用户', 
	title VARCHAR(200) COMMENT '会话标题(可自动生成)', 
	status VARCHAR(16) COMMENT 'active/closed', 
	created_at DATETIME NOT NULL COMMENT '创建时间' DEFAULT now(), 
	updated_at DATETIME NOT NULL COMMENT '更新时间' DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)COMMENT='会话'




CREATE TABLE courses (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	user_id BIGINT NOT NULL COMMENT '所属用户', 
	name VARCHAR(128) NOT NULL COMMENT '课程名', 
	teacher VARCHAR(64) COMMENT '教师', 
	location VARCHAR(128) COMMENT '上课地点', 
	weekday SMALLINT COMMENT '星期(1-7)', 
	start_time TIME COMMENT '开始时间', 
	end_time TIME COMMENT '结束时间', 
	semester VARCHAR(32) COMMENT '学期，如 2025-2026-1', 
	credit DECIMAL(3, 1) COMMENT '学分', 
	start_date DATE COMMENT '学期开始日期', 
	end_date DATE COMMENT '学期结束日期', 
	note TEXT COMMENT '备注', 
	created_at DATETIME NOT NULL COMMENT '创建时间' DEFAULT now(), 
	updated_at DATETIME NOT NULL COMMENT '更新时间' DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)COMMENT='课程'




CREATE TABLE expenses (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	user_id BIGINT NOT NULL COMMENT '所属用户', 
	amount DECIMAL(10, 2) NOT NULL COMMENT '金额(元)', 
	category VARCHAR(32) COMMENT '类别：餐饮/学习/交通/娱乐/生活/other', 
	paid_at DATETIME NOT NULL COMMENT '消费时间', 
	note VARCHAR(255) COMMENT '备注', 
	created_at DATETIME NOT NULL COMMENT '创建时间', 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)COMMENT='消费记录'




CREATE TABLE user_preferences (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	user_id BIGINT NOT NULL COMMENT '用户ID', 
	study_start TIME COMMENT '习惯学习开始时间', 
	study_end TIME COMMENT '习惯学习结束时间', 
	weekly_study_hours DECIMAL(4, 1) COMMENT '每周计划学习时长(小时)', 
	monthly_budget DECIMAL(10, 2) COMMENT '月度总预算', 
	notification_enabled BOOL COMMENT '是否开启提醒', 
	created_at DATETIME NOT NULL COMMENT '创建时间' DEFAULT now(), 
	updated_at DATETIME NOT NULL COMMENT '更新时间' DEFAULT now(), 
	PRIMARY KEY (id), 
	CONSTRAINT uk_pref_user UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)COMMENT='用户偏好'




CREATE TABLE action_plans (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	user_id BIGINT NOT NULL COMMENT '所属用户', 
	conversation_id BIGINT COMMENT '关联对话', 
	title VARCHAR(200) COMMENT '方案标题', 
	goal TEXT COMMENT '总体目标(需求理解)', 
	summary TEXT COMMENT '方案说明', 
	status VARCHAR(16) COMMENT 'draft/active/completed/superseded', 
	replan_of_id BIGINT COMMENT '由哪个旧方案重规划而来', 
	created_at DATETIME NOT NULL COMMENT '创建时间' DEFAULT now(), 
	updated_at DATETIME NOT NULL COMMENT '更新时间' DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(conversation_id) REFERENCES conversations (id), 
	FOREIGN KEY(replan_of_id) REFERENCES action_plans (id)
)COMMENT='行动方案'




CREATE TABLE assignments (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	user_id BIGINT NOT NULL COMMENT '所属用户', 
	course_id BIGINT COMMENT '关联课程(可空)', 
	title VARCHAR(200) NOT NULL COMMENT '作业/课设标题', 
	kind VARCHAR(16) COMMENT 'homework/project/lab/report/other', 
	description TEXT COMMENT '详细要求', 
	deadline DATETIME NOT NULL COMMENT '截止时间', 
	estimated_hours DECIMAL(5, 1) COMMENT '预计耗时(小时)', 
	priority SMALLINT COMMENT '优先级1-5', 
	status VARCHAR(16) COMMENT 'pending/in_progress/completed/overdue', 
	note TEXT COMMENT '备注', 
	created_at DATETIME NOT NULL COMMENT '创建时间' DEFAULT now(), 
	updated_at DATETIME NOT NULL COMMENT '更新时间' DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(course_id) REFERENCES courses (id)
)COMMENT='作业/课程设计'




CREATE TABLE exams (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	user_id BIGINT NOT NULL COMMENT '所属用户', 
	course_id BIGINT COMMENT '关联课程(可空)', 
	name VARCHAR(128) NOT NULL COMMENT '考试名称', 
	exam_date DATE NOT NULL COMMENT '考试日期', 
	start_time TIME COMMENT '开始时间', 
	end_time TIME COMMENT '结束时间', 
	location VARCHAR(128) COMMENT '考试地点', 
	weight DECIMAL(5, 2) COMMENT '成绩占比(%%)', 
	importance SMALLINT COMMENT '重要度1-5', 
	status VARCHAR(16) COMMENT 'pending/done/cancelled', 
	note TEXT COMMENT '备注', 
	created_at DATETIME NOT NULL COMMENT '创建时间' DEFAULT now(), 
	updated_at DATETIME NOT NULL COMMENT '更新时间' DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(course_id) REFERENCES courses (id)
)COMMENT='考试'




CREATE TABLE schedules (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	user_id BIGINT NOT NULL COMMENT '所属用户', 
	day DATE NOT NULL COMMENT '日期', 
	start_time TIME NOT NULL COMMENT '开始时间', 
	end_time TIME NOT NULL COMMENT '结束时间', 
	schedule_type VARCHAR(16) NOT NULL COMMENT 'course/task/activity/exam/free', 
	ref_type VARCHAR(16) COMMENT '来源业务类型', 
	ref_id INTEGER COMMENT '来源业务ID', 
	title VARCHAR(200) COMMENT '标题', 
	location VARCHAR(128) COMMENT '地点', 
	status VARCHAR(16) COMMENT 'planned/done/skipped', 
	conversation_id BIGINT COMMENT '产生该日程的对话', 
	created_at DATETIME NOT NULL COMMENT '创建时间' DEFAULT now(), 
	updated_at DATETIME NOT NULL COMMENT '更新时间' DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(conversation_id) REFERENCES conversations (id)
)COMMENT='日程'




CREATE TABLE tasks (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	user_id BIGINT NOT NULL COMMENT '所属用户', 
	title VARCHAR(200) NOT NULL COMMENT '任务标题', 
	description TEXT COMMENT '任务说明', 
	task_type VARCHAR(16) COMMENT 'academic/schedule/finance/general', 
	source_type VARCHAR(16) COMMENT '来源：exam/assignment/activity/manual/agent', 
	source_id BIGINT COMMENT '来源对象ID(暂存其业务表ID)', 
	priority SMALLINT COMMENT '优先级1-5', 
	status VARCHAR(16) COMMENT 'pending/planned/in_progress/done/postponed/cancelled/overdue', 
	deadline DATETIME COMMENT '截止时间', 
	estimated_hours DECIMAL(5, 1) COMMENT '预计耗时(小时)', 
	plan_date DATE COMMENT '计划执行日期', 
	actual_hours DECIMAL(5, 1) COMMENT '实际耗时(小时)', 
	conversation_id BIGINT COMMENT '产生该任务的对话', 
	created_at DATETIME NOT NULL COMMENT '创建时间' DEFAULT now(), 
	updated_at DATETIME NOT NULL COMMENT '更新时间' DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(source_id) REFERENCES tasks (id), 
	FOREIGN KEY(conversation_id) REFERENCES conversations (id)
)COMMENT='综合任务'




CREATE TABLE action_plan_items (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	plan_id BIGINT NOT NULL COMMENT '所属方案', 
	task_id BIGINT COMMENT '关联任务(可空)', 
	content VARCHAR(500) NOT NULL COMMENT '执行内容', 
	reason VARCHAR(500) COMMENT '如此安排的原因', 
	day DATE COMMENT '计划日期', 
	start_time TIME COMMENT '开始时间', 
	end_time TIME COMMENT '结束时间', 
	status VARCHAR(16) COMMENT 'pending/in_progress/done/postponed', 
	sort_order INTEGER COMMENT '排序', 
	created_at DATETIME NOT NULL COMMENT '创建时间', 
	PRIMARY KEY (id), 
	FOREIGN KEY(plan_id) REFERENCES action_plans (id), 
	FOREIGN KEY(task_id) REFERENCES tasks (id)
)COMMENT='行动方案明细'




CREATE TABLE agent_sessions (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	user_id BIGINT NOT NULL COMMENT '所属用户', 
	conversation_id BIGINT COMMENT '关联对话', 
	input_text TEXT NOT NULL COMMENT '原始用户需求', 
	status VARCHAR(16) COMMENT 'queued/running/completed/failed', 
	current_agent VARCHAR(32) COMMENT '当前执行中的 Agent', 
	result TEXT COMMENT '最终汇总结果/回答文本', 
	plan_id BIGINT COMMENT '本轮生成的行动方案', 
	replan_of_id BIGINT COMMENT '由哪次执行触发的重规划', 
	started_at DATETIME COMMENT '开始时间', 
	ended_at DATETIME COMMENT '结束时间', 
	created_at DATETIME NOT NULL COMMENT '创建时间', 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(conversation_id) REFERENCES conversations (id), 
	FOREIGN KEY(plan_id) REFERENCES action_plans (id), 
	FOREIGN KEY(replan_of_id) REFERENCES agent_sessions (id)
)COMMENT='Agent执行会话'




CREATE TABLE task_dependencies (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	task_id BIGINT NOT NULL COMMENT '后置任务', 
	depends_on_task_id BIGINT NOT NULL COMMENT '前置任务', 
	PRIMARY KEY (id), 
	CONSTRAINT uk_task_dep UNIQUE (task_id, depends_on_task_id), 
	FOREIGN KEY(task_id) REFERENCES tasks (id), 
	FOREIGN KEY(depends_on_task_id) REFERENCES tasks (id)
)COMMENT='任务依赖'




CREATE TABLE agent_actions (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	session_id BIGINT NOT NULL COMMENT '所属执行会话', 
	agent_name VARCHAR(32) NOT NULL COMMENT '执行 Agent', 
	action VARCHAR(32) NOT NULL COMMENT 'understand/decompose/analyze/tool_call/aggregate/replan', 
	status VARCHAR(16) COMMENT 'running/completed/failed', 
	request TEXT COMMENT '动作输入(JSON/文本)', 
	response TEXT COMMENT '动作输出(JSON/文本)', 
	started_at DATETIME COMMENT '开始时间', 
	ended_at DATETIME COMMENT '结束时间', 
	PRIMARY KEY (id), 
	FOREIGN KEY(session_id) REFERENCES agent_sessions (id)
)COMMENT='Agent动作记录'




CREATE TABLE messages (
	id BIGINT NOT NULL AUTO_INCREMENT, 
	conversation_id BIGINT NOT NULL COMMENT '所属会话', 
	`role` VARCHAR(16) NOT NULL COMMENT 'user/assistant/system/agent', 
	content TEXT COMMENT '消息内容', 
	agent_name VARCHAR(32) COMMENT '若为 agent 消息，记录来源 Agent', 
	session_id BIGINT COMMENT '关联的 Agent 执行会话', 
	created_at DATETIME NOT NULL COMMENT '创建时间', 
	PRIMARY KEY (id), 
	FOREIGN KEY(conversation_id) REFERENCES conversations (id), 
	FOREIGN KEY(session_id) REFERENCES agent_sessions (id)
)COMMENT='消息'


