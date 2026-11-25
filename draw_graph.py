from app.ai.graph import rag_graph

graph = rag_graph.get_graph()
mermaid = graph.draw_mermaid()

with open("workflow.mmd", "w", encoding="utf-8") as f:
    f.write(mermaid)
print(mermaid)

try:
    with open("workflow.png", "wb") as f:
        f.write(graph.draw_mermaid_png())
    print("\nSaved workflow.png")
except Exception as e:
    print("\nPNG download failed:", e)
    print(
        "Paste the contents of workflow.mmd into https://mermaid.live to get the image."
    )
