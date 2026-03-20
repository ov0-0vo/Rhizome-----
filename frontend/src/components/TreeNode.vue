<template>
  <div class="tree-node">
    <div class="node-content" @click="expanded = !expanded">
      <span class="expand-icon">{{ hasChildren ? (expanded ? '📂' : '📁') : '📄' }}</span>
      <span class="node-name">{{ node.name }}</span>
      <span class="knowledge-count">({{ node.knowledge_count }} 条知识)</span>
    </div>
    <div v-if="hasChildren && expanded" class="children">
      <TreeNode 
        v-for="child in node.children" 
        :key="child.id" 
        :node="child"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  node: {
    type: Object,
    required: true
  }
})

const expanded = ref(true)

const hasChildren = computed(() => {
  return props.node.children && props.node.children.length > 0
})
</script>

<style scoped>
.tree-node {
  margin-left: 20px;
}

.tree-node:first-child {
  margin-left: 0;
}

.node-content {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 6px;
  transition: background-color 0.2s;
}

.node-content:hover {
  background-color: var(--bg-color);
}

.expand-icon {
  margin-right: 8px;
  font-size: 16px;
}

.node-name {
  font-weight: 500;
}

.knowledge-count {
  margin-left: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}

.children {
  border-left: 2px solid var(--border-color);
  margin-left: 12px;
  padding-left: 8px;
}
</style>
