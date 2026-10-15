"""Effect type of a tool, from its name: read, create, send, overwrite, trigger, delete or unclear.

Send and trigger split out of the create/update verbs because they act outside the resource
(a message leaves, a job or payment starts) and cannot be undone by editing it back.
"""
from profile_tools import VERB2, name_verb, split_name

SEND = {"send", "submit", "post", "publish", "reply", "notify", "email", "message", "share", "invite",
        "tweet", "broadcast", "forward", "comment"}
TRIGGER = {"start", "trigger", "launch", "deploy", "buy", "pay", "purchase", "order",
           "checkout", "book", "apply", "join", "transfer", "trade", "swap", "invoke", "dispatch", "restart"}
NAMES = {"read": "read", "create": "create", "update": "overwrite", "destructive": "delete"}


def effect(name):
    v, _ = name_verb(split_name(name))
    if v is None:
        return "unclear"
    head = v.split("_")[0]
    if head in SEND:
        return "send"
    if head in TRIGGER:
        return "trigger"
    return NAMES[VERB2[v][0]]


if __name__ == "__main__":
    assert effect("run_query") != "trigger" and effect("execute_sql") != "trigger"
    for n, e in [("list_events", "read"), ("create_event", "create"), ("send_email", "send"),
                 ("update_schedule", "overwrite"), ("start_workflow", "trigger"), ("deleteInvoice", "delete")]:
        assert effect(n) == e, (n, effect(n))
    print("ok")
