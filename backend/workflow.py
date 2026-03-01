from langgraph.graph import START, END, StateGraph
from backend.nodes import (
    State,
    query_gen_node,
    query_validation_node,
    execute_query_node,
    final_output_node,
    should_continue
)

workflow = StateGraph(State)

workflow.add_node("query_gen",        query_gen_node)
workflow.add_node("query_validation", query_validation_node)
workflow.add_node("execute_query",    execute_query_node)
workflow.add_node("final_output",     final_output_node)

workflow.add_edge(START,              "query_gen")
workflow.add_edge("query_gen",        "query_validation")
workflow.add_conditional_edges("query_validation", should_continue)
workflow.add_edge("execute_query",    "final_output")
workflow.add_edge("final_output",     END)

app_graph = workflow.compile()