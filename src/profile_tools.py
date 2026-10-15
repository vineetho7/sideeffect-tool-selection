"""Rule-based operation profile per tool: (op class, severity, resource, signal used).

Severity taxonomy (study-specific, validated manually on a sample):
0 read  - no state change          1 create - adds new state
2 update - mutates existing state  3 destructive - deletes / irreversible
"""
import re
from collections import Counter

READ = {"get", "list", "search", "find", "query", "fetch", "read", "show", "describe", "view",
        "retrieve", "lookup", "count", "check", "inspect", "browse", "download", "explain",
        "analyze", "analyse", "summarize", "status", "info", "preview", "compare", "diff",
        "lookup", "resolve_id", "estimate", "calculate", "validate", "verify", "explore",
        "scan", "detect", "recommend", "suggest", "convert", "parse", "extract", "translate",
        "render", "format", "lint", "test", "ping", "health", "whoami", "me", "load", "export",
        "discover", "poll", "watch", "tail", "grep", "ls", "cat", "head", "stat", "has", "is",
        "can", "exists", "audit", "trace", "profile", "measure", "monitor", "evaluate", "score",
        "rank", "classify", "predict", "forecast", "visualize", "plot", "chart", "screenshot",
        "capture", "navigate", "scrape", "crawl", "research", "ask", "chat", "answer", "think",
        "assess", "compute", "quote", "decode", "diagnose", "enrich", "summarise", "review",
        "identify", "match", "geocode", "forecast", "simulate", "lookup", "sample", "resolve"}
CREATE = {"create", "add", "new", "post", "insert", "upload", "register", "open", "make",
          "clone", "fork", "copy", "import", "invite", "comment", "reply", "schedule", "book",
          "submit", "send", "publish", "generate", "draft", "duplicate", "provision", "spawn",
          "launch", "init", "initialize", "attach", "link", "tag", "label", "star", "follow",
          "subscribe", "save", "store", "remember", "log", "record", "track", "enqueue", "push",
          "share", "request", "mint", "emit", "notify", "message", "email", "tweet",
          "commit", "build", "bookmark", "pin", "favorite", "react", "vote", "like", "upsert"}
UPDATE = {"update", "edit", "modify", "set", "patch", "put", "rename", "move", "change",
          "assign", "unassign", "close", "reopen", "merge", "restart", "stop", "start", "enable",
          "disable", "toggle", "approve", "reject", "resolve", "archive", "unarchive", "lock",
          "unlock", "apply", "deploy", "run", "execute", "exec", "replace", "write", "sync",
          "transfer", "cancel", "scale", "rollback", "trigger", "invoke", "configure", "reset",
          "rotate", "pause", "resume", "suspend", "activate", "deactivate", "mark", "complete",
          "transition", "reorder", "sort", "fill", "click", "type", "press", "select", "hover",
          "drag", "upgrade", "downgrade", "install", "migrate", "promote", "restore", "refresh",
          "reindex", "rebuild", "retry", "rerun", "dispatch", "release", "pay", "charge",
          "refund", "swap", "stake", "bridge", "trade", "buy", "sell", "order", "withdraw",
          "deposit", "mute", "unmute", "hide", "unhide", "grant", "unpin", "unstar", "unfollow",
          "unsubscribe", "unlink", "detach", "untag", "unlabel", "dismiss", "accept", "decline",
          "confirm", "respond", "join", "leave", "claim", "evaluate_script", "eval", "sign", "verify_domain", "connect",
          "disconnect", "login", "logout", "authorize", "authenticate", "shutdown", "reboot"}
DESTRUCTIVE = {"delete", "remove", "drop", "destroy", "purge", "erase", "wipe", "terminate",
               "kill", "truncate", "uninstall", "unpublish", "revoke", "ban", "clear",
               "empty", "nuke", "deregister", "unregister", "rm", "rmdir", "trash", "discard",
               "force_push", "burn", "evict", "expunge", "deprovision", "teardown", "flush"}

OPS = [("read", 0, READ), ("create", 1, CREATE), ("update", 2, UPDATE), ("destructive", 3, DESTRUCTIVE)]
VERB2 = {}
for op, sev, vs in OPS:
    for v in vs:
        VERB2.setdefault(v, (op, sev))
SEV = {"read": 0, "create": 1, "update": 2, "destructive": 3}

STOP = {"a", "an", "the", "by", "for", "of", "in", "on", "to", "from", "with", "all", "and",
        "or", "my", "your", "id", "ids", "info", "details", "detail", "data", "item", "items",
        "tool", "mcp", "api", "v1", "v2", "v3", "single", "one", "multiple", "bulk", "batch",
        "many", "current", "latest", "new", "existing", "specific", "using", "via", "as"}
ALIAS = {"pr": "pull_request", "prs": "pull_request", "pullrequest": "pull_request",
         "repo": "repository", "repos": "repository", "msg": "message", "dir": "directory",
         "folder": "directory", "db": "database", "doc": "document", "docs": "document",
         "env": "environment", "vm": "instance", "k8s": "kubernetes", "ns": "namespace",
         "config": "configuration", "cfg": "configuration", "org": "organization",
         "ws": "workspace", "proj": "project", "txn": "transaction", "tx": "transaction"}


def split_name(name):
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", s)
    return [w for w in re.split(r"[^A-Za-z0-9]+", s.lower()) if w]


def singular(w):
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 4 and re.search(r"(ss|sh|ch|x|z)es$", w):
        return w[:-2]
    if len(w) > 3 and w.endswith("s") and not w.endswith(("ss", "us", "is")):
        return w[:-1]
    return w


# Words that are usually nouns in tool names; only read as verbs in leading position.
AMBIG = {"issue", "log", "tag", "label", "order", "request", "message", "email", "record",
         "type", "link", "test", "status", "info", "chart", "plot", "profile", "score",
         "trace", "comment", "book", "post", "commit", "push", "release", "schedule",
         "export", "import", "copy", "draft", "star", "pin", "vote", "like", "react", "track",
         "store", "sort", "select", "fill", "monitor", "me", "has", "is", "can", "health",
         "watch", "ask", "answer", "chat", "think", "load", "run", "rank", "stat", "head",
         "cat", "ls", "grep", "tail", "share", "save", "set", "new", "open", "order", "mark",
         "format", "capture", "screenshot", "lint", "diff", "config", "query", "audit",
         "remember", "note", "notify", "tweet", "sign", "eval", "transfer", "trade", "swap"}
TICKETISH = {"issue", "ticket", "incident", "alert", "conversation", "comment", "thread",
             "conflict", "review", "bug", "case", "task", "finding", "problem"}
PREP = {"from", "in", "to", "for", "by", "on", "with", "into", "at", "of", "as", "via"}
COMPOUND = {"pull_request", "merge_request", "access_token", "api_key", "workflow_run",
            "check_run", "service_account", "pull_request_review", "code_scanning",
            "secret_scanning", "page_view", "user_story", "time_entry", "line_item"}


def name_verb(tokens):
    """Returns (verb, index of the verb's last token). Unambiguous verbs anywhere win;
    noun-like verbs count only in the first two positions."""
    def at(i):
        t = tokens[i]
        if i + 1 < len(tokens) and f"{t}_{tokens[i+1]}" in VERB2:
            return f"{t}_{tokens[i+1]}", i + 1
        return (t, i) if t in VERB2 else (None, None)
    for i in range(len(tokens)):
        v, j = at(i)
        if v and v not in AMBIG:
            return v, j
    for i in range(min(2, len(tokens))):
        v, j = at(i)
        if v:
            return v, j
    return None, None


def resource_of(tokens, vi, server_tokens=()):
    rest = tokens[vi + 1:] if vi is not None else tokens
    if vi is not None and not [w for w in rest if w not in STOP]:   # verb-last: issue_create
        rest = tokens[:vi]
    cut = []
    for w in rest:                              # stop at a preposition: label_from_issue -> label
        if w in PREP and cut:
            break
        cut.append(w)
    words = [ALIAS.get(w, singular(w)) for w in cut if w not in STOP and w not in PREP
             and not w.isdigit() and w not in server_tokens]
    if not words:
        return ""
    for n in (3, 2):
        j = "_".join(words[:n])
        if j in COMPOUND:
            return j
    return words[0]


def annotation_op(ann):
    if not isinstance(ann, dict):
        return None
    ro, de = ann.get("readOnlyHint"), ann.get("destructiveHint")
    if ro is True:
        return "read"
    if ro is False and de is True:
        return "destructive"
    if ro is False and de is False:
        return "write"                          # create or update, unspecified
    return None


def profile(tool, server_tokens=()):
    toks = split_name(tool["name"])
    verb, vi = name_verb(toks)
    if verb is None:
        # fall back to the first word of the description ("Deletes a ...", "Lists ...")
        dw = split_name((tool.get("description") or "")[:80])
        for w in dw[:3]:
            w2 = w[:-1] if w.endswith("s") and w[:-1] in VERB2 else w
            w2 = w2[:-2] if w2.endswith("es") and w2[:-2] in VERB2 else w2
            if w2 in VERB2:
                verb = w2
                break
        src = "description" if verb else "none"
    else:
        src = "name"
    op, sev = VERB2.get(verb, (None, None))
    res = resource_of(toks, vi, server_tokens)
    if verb == "resolve" and res in TICKETISH:
        op, sev = "update", 2
    return {"verb": verb, "op": op, "sev": sev, "resource": res,
            "src": src, "ann_op": annotation_op(tool.get("annotations"))}


if __name__ == "__main__":
    for n in ["list_pull_requests", "createIssue", "delete_repo", "get-file-contents",
              "github_merge_pull_request", "issue_create", "force_push_branch", "search_code",
              "k8s_scale_deployment", "removeLabelFromIssue", "browser_click"]:
        print(n, profile({"name": n}))
    assert profile({"name": "list_pull_requests"})["resource"] == "pull_request"
    assert profile({"name": "delete_repo"})["sev"] == 3
    assert profile({"name": "issue_create"})["resource"] == "issue"
    assert profile({"name": "createIssue"})["op"] == "create"


def hybrid_sev(t):
    """System profile: trust the server's own hint where it is decisive, else the name rules."""
    a = t.get("ann_op")
    if a == "read":
        return 0
    if a == "destructive":
        return 3
    if a == "write":
        return t["sev"] if t["sev"] in (1, 2) else 2
    return t["sev"]
