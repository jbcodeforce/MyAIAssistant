--
-- PostgreSQL database dump
--

\restrict uQuuouNK3IwfykODm4IRVbVbOY92qKxGXPalQK0t39oUYJqeA5Kab5QfDonCt4H

-- Dumped from database version 16.11
-- Dumped by pg_dump version 16.11

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: knowledge; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.knowledge (
    id integer NOT NULL,
    title character varying(255) NOT NULL,
    description text,
    document_type character varying(50) NOT NULL,
    uri character varying(2048) NOT NULL,
    category character varying(100),
    tags character varying(500),
    content_hash character varying(64),
    status character varying(50) NOT NULL,
    referenced_at timestamp without time zone DEFAULT now() NOT NULL,
    last_fetched_at timestamp without time zone,
    indexed_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.knowledge OWNER TO postgres;

--
-- Name: knowledge_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.knowledge_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.knowledge_id_seq OWNER TO postgres;

--
-- Name: knowledge_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.knowledge_id_seq OWNED BY public.knowledge.id;


--
-- Name: organizations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.organizations (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    stakeholders text,
    team text,
    description text,
    related_products text,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.organizations OWNER TO postgres;

--
-- Name: organizations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.organizations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.organizations_id_seq OWNER TO postgres;

--
-- Name: organizations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.organizations_id_seq OWNED BY public.organizations.id;


--
-- Name: projects; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.projects (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    organization_id integer,
    status character varying(50) NOT NULL,
    tasks text,
    past_steps text,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.projects OWNER TO postgres;

--
-- Name: projects_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.projects_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.projects_id_seq OWNER TO postgres;

--
-- Name: projects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.projects_id_seq OWNED BY public.projects.id;


--
-- Name: settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.settings (
    id integer NOT NULL,
    llm_provider character varying(100),
    llm_name character varying(100),
    llm_api_endpoint character varying(2048),
    api_key character varying(500),
    default_temperature double precision,
    chunk_size integer,
    overlap integer,
    min_chunk_size integer,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.settings OWNER TO postgres;

--
-- Name: settings_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.settings_id_seq OWNER TO postgres;

--
-- Name: settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.settings_id_seq OWNED BY public.settings.id;


--
-- Name: task_plans; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.task_plans (
    id integer NOT NULL,
    todo_id integer NOT NULL,
    content text NOT NULL,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.task_plans OWNER TO postgres;

--
-- Name: task_plans_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.task_plans_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.task_plans_id_seq OWNER TO postgres;

--
-- Name: task_plans_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.task_plans_id_seq OWNED BY public.task_plans.id;


--
-- Name: todos; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.todos (
    id integer NOT NULL,
    title character varying(255) NOT NULL,
    description text,
    status character varying(50) NOT NULL,
    urgency character varying(50),
    importance character varying(50),
    category character varying(100),
    project_id integer,
    created_at timestamp without time zone DEFAULT now() NOT NULL,
    updated_at timestamp without time zone DEFAULT now() NOT NULL,
    completed_at timestamp without time zone,
    due_date timestamp without time zone,
    source_type character varying(50),
    source_id integer
);


ALTER TABLE public.todos OWNER TO postgres;

--
-- Name: todos_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.todos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.todos_id_seq OWNER TO postgres;

--
-- Name: todos_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.todos_id_seq OWNED BY public.todos.id;


--
-- Name: knowledge id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.knowledge ALTER COLUMN id SET DEFAULT nextval('public.knowledge_id_seq'::regclass);


--
-- Name: organizations id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.organizations ALTER COLUMN id SET DEFAULT nextval('public.organizations_id_seq'::regclass);


--
-- Name: projects id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.projects ALTER COLUMN id SET DEFAULT nextval('public.projects_id_seq'::regclass);


--
-- Name: settings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.settings ALTER COLUMN id SET DEFAULT nextval('public.settings_id_seq'::regclass);


--
-- Name: task_plans id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_plans ALTER COLUMN id SET DEFAULT nextval('public.task_plans_id_seq'::regclass);


--
-- Name: todos id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.todos ALTER COLUMN id SET DEFAULT nextval('public.todos_id_seq'::regclass);


--
-- Data for Name: knowledge; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.knowledge (id, title, description, document_type, uri, category, tags, content_hash, status, referenced_at, last_fetched_at, indexed_at, created_at, updated_at) FROM stdin;
1	Confluent Cloud Flink Doc		folder	file:///Users/jerome/Documents/Code/ReadOnlyRepos/quickstart-streaming-agents/assets/lab2/flink_docs	Confluent_flink		2f9424ffbe538c3cf063dd59e2fd201a4713a6db201816b2457f33f26952c62c	active	2025-12-23 17:32:00	2025-12-26 20:39:43.151501	2025-12-26 20:39:43.151501	2025-12-23 17:32:00	2025-12-26 20:39:43
2	Few-shot prompting guide		website	https://www.promptingguide.ai/techniques/fewshot			f89888662b791901b5d69b1fc8a17f4c3cdc24c511452b0a7f0ab37d75963f74	active	2025-12-26 19:57:29	2025-12-26 19:58:11.557634	2025-12-26 19:58:11.557634	2025-12-26 19:57:29	2025-12-26 19:58:11
\.


--
-- Data for Name: organizations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.organizations (id, name, stakeholders, team, description, related_products, created_at, updated_at) FROM stdin;
1	AI.org	me	None	Deploy MyAiAssistant	MyAIAssistant, and some dedicated agents	2025-12-22 17:45:48	2025-12-29 18:03:45
\.


--
-- Data for Name: projects; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.projects (id, name, description, organization_id, status, tasks, past_steps, created_at, updated_at) FROM stdin;
1	Knowledge Management Project	Finalize knowledge management and chat on km	1	Active	- tool to ingest from folder\n- UI to support referencing a folder\n- Clear documentation for how to manage knowledge	\N	2025-12-22 17:48:23	2025-12-29 18:14:52
\.


--
-- Data for Name: settings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.settings (id, llm_provider, llm_name, llm_api_endpoint, api_key, default_temperature, chunk_size, overlap, min_chunk_size, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: task_plans; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.task_plans (id, todo_id, content, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: todos; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.todos (id, title, description, status, urgency, importance, category, project_id, created_at, updated_at, completed_at, due_date, source_type, source_id) FROM stdin;
1	Finalize the Knowledge management user experience		Started	Not Urgent	Important	platform	1	2025-12-22 17:51:16	2025-12-29 19:40:56	\N	2025-12-24 09:51:00	\N	\N
2	Finalize the user guide		Started	Urgent	Important	\N	1	2025-12-23 01:55:24	2025-12-29 19:05:18	\N	2026-01-03 17:55:00	\N	\N
3	Add metrics to the MyAIAssistant app		Open	\N	\N	\N	\N	2025-12-29 19:10:38	2025-12-29 19:10:38	\N	2026-01-04 11:10:00	\N	\N
\.


--
-- Name: knowledge_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.knowledge_id_seq', 2, true);


--
-- Name: organizations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.organizations_id_seq', 1, true);


--
-- Name: projects_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.projects_id_seq', 1, true);


--
-- Name: settings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.settings_id_seq', 1, false);


--
-- Name: task_plans_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.task_plans_id_seq', 1, false);


--
-- Name: todos_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.todos_id_seq', 3, true);


--
-- Name: knowledge knowledge_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.knowledge
    ADD CONSTRAINT knowledge_pkey PRIMARY KEY (id);


--
-- Name: organizations organizations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT organizations_pkey PRIMARY KEY (id);


--
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- Name: settings settings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.settings
    ADD CONSTRAINT settings_pkey PRIMARY KEY (id);


--
-- Name: task_plans task_plans_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_plans
    ADD CONSTRAINT task_plans_pkey PRIMARY KEY (id);


--
-- Name: task_plans task_plans_todo_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_plans
    ADD CONSTRAINT task_plans_todo_id_key UNIQUE (todo_id);


--
-- Name: todos todos_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.todos
    ADD CONSTRAINT todos_pkey PRIMARY KEY (id);


--
-- Name: projects projects_organization_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES public.organizations(id);


--
-- Name: task_plans task_plans_todo_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.task_plans
    ADD CONSTRAINT task_plans_todo_id_fkey FOREIGN KEY (todo_id) REFERENCES public.todos(id) ON DELETE CASCADE;


--
-- Name: todos todos_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.todos
    ADD CONSTRAINT todos_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- PostgreSQL database dump complete
--

\unrestrict uQuuouNK3IwfykODm4IRVbVbOY92qKxGXPalQK0t39oUYJqeA5Kab5QfDonCt4H

