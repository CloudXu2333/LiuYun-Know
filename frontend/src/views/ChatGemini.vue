<template>
  <div class="min-h-screen h-screen bg-gemini-bg flex flex-col overflow-hidden font-sans">
    <!-- 顶部导航栏 - Gemini 风格 -->
    <header class="glass-gemini border-b border-gemini-border sticky top-0 z-50">
      <div class="w-full px-4">
        <div class="flex justify-between items-center h-14">
          <!-- 左侧 - Logo 和菜单按钮（固定位置） -->
          <div class="flex items-center space-x-3">
            <div class="flex items-center space-x-2 cursor-pointer" @click="router.push('/')">
              <div class="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-sm">
                <span class="text-white text-xs font-bold">L</span>
              </div>
              <span class="text-lg font-semibold text-gemini-text-primary tracking-tight">LiuYun</span>
            </div>
            
            <button
              @click="toggleSidebar"
              class="btn-gemini-icon text-gemini-text-secondary hover:bg-gemini-bg/80"
              title="菜单"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
              </svg>
            </button>
          </div>

          <!-- 中间标题 -->
          <div class="flex-1 flex justify-center">
            <h1 class="text-sm font-medium text-gemini-text-secondary opacity-0 transition-opacity duration-300 hidden md:block" :class="{ 'opacity-100': currentConversationTitle }">
              {{ currentConversationTitle || '新对话' }}
            </h1>
          </div>

          <!-- 右侧操作 -->
          <div class="flex items-center space-x-3">
            <!-- 流程图按钮 -->
            <button
              @click="router.push('/diagram')"
              class="btn-gemini-icon text-gemini-text-secondary"
              title="AI 流程图"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2"></path>
              </svg>
            </button>

            <button
              @click="handleNewChat"
              class="btn-gemini-icon text-gemini-text-secondary"
              title="新对话"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
              </svg>
            </button>

            <!-- 用户菜单 -->
            <div class="relative" ref="userMenuRef">
              <button
                @click="toggleUserMenu"
                class="btn-gemini-icon p-1"
              >
                <div class="w-8 h-8 rounded-full bg-gradient-to-br from-gemini-blue-500 to-gemini-purple-500 flex items-center justify-center text-white text-sm font-medium shadow-md">
                  {{ userInitial }}
                </div>
              </button>

              <!-- 下拉菜单 -->
              <transition
                enter-active-class="transition ease-out duration-200"
                enter-from-class="transform opacity-0 scale-95"
                enter-to-class="transform opacity-100 scale-100"
                leave-active-class="transition ease-in duration-75"
                leave-from-class="transform opacity-100 scale-100"
                leave-to-class="transform opacity-0 scale-95"
              >
                <div
                  v-show="showUserMenu"
                  class="absolute right-0 mt-2 w-56 rounded-xl shadow-gemini-xl bg-white ring-1 ring-black ring-opacity-5 focus:outline-none py-2"
                >
                  <div class="px-4 py-3 border-b border-gray-100">
                    <p class="text-sm font-medium text-gray-900">{{ authStore.user?.username }}</p>
                    <p class="text-xs text-gray-500 truncate">{{ authStore.user?.email }}</p>
                  </div>
                  <!-- 管理员入口 -->
                  <button
                    v-if="authStore.user?.is_superuser"
                    @click="goToAdminUsers"
                    class="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 transition-colors flex items-center"
                  >
                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"></path></svg>
                    用户管理
                  </button>
                  <button
                    @click="handleLogout"
                    class="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 transition-colors flex items-center"
                  >
                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path></svg>
                    登出
                  </button>
                </div>
              </transition>
            </div>
          </div>
        </div>
      </div>
    </header>

    <!-- 主要内容区域 -->
    <div class="flex-1 flex overflow-hidden relative">
      <!-- 侧边栏 - 对话历史 -->
      <aside
        v-show="showSidebar"
        :style="{ width: sidebarWidth + 'px' }"
        class="relative bg-gemini-surface border-r border-gemini-border flex flex-col shadow-xl"
        :class="[
          showSidebar ? 'translate-x-0' : '-translate-x-full',
          !isResizing ? 'transition-transform duration-300 ease-in-out' : ''
        ]"
      >
        <!-- 对话历史区域 -->
        <div class="p-4 border-b border-gemini-border bg-gemini-bg/50 backdrop-blur-sm">
          <h2 class="text-sm font-medium text-gemini-text-primary flex items-center">
            <svg class="w-4 h-4 mr-2 text-gemini-text-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
            近期对话
          </h2>
        </div>
        <div class="flex-1 overflow-y-auto scrollbar-gemini p-3 space-y-1">
          <div
            v-for="conv in conversations"
            :key="conv.id"
            @click="loadConversation(conv.id)"
            class="group flex items-center p-3 rounded-lg cursor-pointer transition-all duration-200"
            :class="currentConversationId === conv.id ? 'bg-gemini-blue-50 text-gemini-blue-700 shadow-sm' : 'hover:bg-gemini-bg text-gemini-text-secondary'"
          >
            <svg class="w-4 h-4 mr-3 flex-shrink-0 opacity-50 group-hover:opacity-100 transition-opacity" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"></path></svg>
            <div class="flex-1 min-w-0">
              <!-- 编辑标题模式 -->
              <input
                v-if="editingConvId === conv.id"
                v-model="editingTitle"
                @blur="saveTitle(conv.id)"
                @keydown.enter="saveTitle(conv.id)"
                @keydown.esc="cancelEdit"
                class="text-sm font-medium w-full bg-white px-2 py-1 rounded border border-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
                @click.stop
                :ref="el => { if (el && editingConvId === conv.id) titleInput = el }"
              />
              <!-- 显示标题模式 -->
              <p v-else class="text-sm font-medium truncate" @dblclick="startEdit(conv)">
                {{ conv.title || '新对话' }}
              </p>
              <p class="text-xs text-gemini-text-tertiary mt-0.5 opacity-0 group-hover:opacity-100 transition-opacity duration-200">{{ formatDate(conv.updated_at) }}</p>
            </div>
            <!-- 编辑按钮 -->
            <button
              v-if="!editingConvId"
              @click.stop="startEdit(conv)"
              class="opacity-0 group-hover:opacity-100 p-1 hover:bg-gray-200 rounded transition-all"
              title="编辑标题"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path>
              </svg>
            </button>
            <!-- 删除按钮 -->
            <button
              v-if="!editingConvId"
              @click.stop="confirmDeleteConversation(conv)"
              class="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 hover:text-red-600 rounded transition-all"
              title="删除对话"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
              </svg>
            </button>
          </div>
        </div>
        
        <!-- 底部按钮组 -->
        <div class="p-3 border-t border-gemini-border bg-gemini-bg/30 space-y-2">
          <!-- 长期记忆按钮 -->
          <button
            @click="router.push('/memory')"
            class="w-full flex items-center justify-center space-x-2 px-4 py-2.5 rounded-lg bg-gradient-to-r from-purple-500 to-indigo-600 text-white hover:from-purple-600 hover:to-indigo-700 transition-all duration-200 shadow-md hover:shadow-lg transform hover:scale-[1.02] active:scale-[0.98]"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
            </svg>
            <span class="font-medium">长期记忆</span>
          </button>
          <!-- 知识库管理按钮 -->
          <button
            @click="router.push('/knowledge')"
            class="w-full flex items-center justify-center space-x-2 px-4 py-2.5 rounded-lg bg-gradient-to-r from-blue-500 to-cyan-600 text-white hover:from-blue-600 hover:to-cyan-700 transition-all duration-200 shadow-md hover:shadow-lg transform hover:scale-[1.02] active:scale-[0.98]"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
            </svg>
            <span class="font-medium">知识库管理</span>
          </button>
        </div>
        
        <!-- 拖拽调整宽度的手柄 -->
        <div
          @mousedown="startResize"
          class="absolute top-0 right-0 w-1 h-full cursor-ew-resize hover:bg-blue-400 transition-colors group"
          title="拖拽调整宽度"
        >
          <div class="absolute top-1/2 right-0 transform -translate-y-1/2 w-1 h-12 bg-gray-300 group-hover:bg-blue-400 rounded-l transition-colors"></div>
        </div>
      </aside>

      <!-- 聊天区域 -->
      <main class="flex-1 flex flex-col min-w-0 bg-white relative">
        <div ref="chatContainer" class="flex-1 overflow-y-auto scrollbar-gemini scroll-smooth" @scroll="handleChatScroll">
          <div class="max-w-4xl mx-auto px-4 py-8">
            <!-- 欢迎界面 -->
            <transition
              enter-active-class="transition ease-out duration-500"
              enter-from-class="opacity-0 translate-y-10"
              enter-to-class="opacity-100 translate-y-0"
              leave-active-class="transition ease-in duration-300"
              leave-from-class="opacity-100 translate-y-0"
              leave-to-class="opacity-0 -translate-y-10"
            >
              <div v-if="messages.length === 0" class="flex flex-col items-center justify-center min-h-[60vh]">
                <!-- Gemini Logo -->
                <div class="relative mb-8 group">
                  <div class="w-24 h-24 rounded-3xl bg-gradient-to-br from-blue-400 via-purple-500 to-red-400 flex items-center justify-center shadow-gemini-xl transform group-hover:scale-105 transition-transform duration-500">
                    <svg class="w-12 h-12 text-white" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M15.25,18L14,14.25L10.25,13L14,11.75L15.25,8L16.5,11.75L20.25,13L16.5,14.25L15.25,18Z"></path>
                    </svg>
                  </div>
                  <!-- 光晕效果 -->
                  <div class="absolute inset-0 rounded-3xl bg-gradient-to-br from-blue-400 via-purple-500 to-red-400 opacity-20 blur-2xl animate-pulse-soft"></div>
                </div>

                <h1 class="text-4xl md:text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-purple-600 to-red-500 mb-6 tracking-tight">
                  你好，我是 LiuYun
                </h1>
                <p class="text-xl text-gemini-text-secondary mb-12 text-center max-w-2xl leading-relaxed">
                  我可以帮你回答问题、提供信息、协助创作，或者陪你聊聊天。
                </p>

                <!-- 建议卡片 -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-3xl px-4">
                  <button
                    v-for="(suggestion, index) in suggestions"
                    :key="index"
                    @click="handleSuggestion(suggestion.text)"
                    class="group relative overflow-hidden bg-gemini-surface p-5 rounded-2xl border border-gemini-border hover:border-blue-200 hover:shadow-lg transition-all duration-300 text-left"
                  >
                    <div class="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-blue-50 to-purple-50 rounded-bl-full -mr-10 -mt-10 transition-transform group-hover:scale-150 duration-500"></div>
                    <div class="relative z-10 flex items-start space-x-4">
                      <div class="w-10 h-10 rounded-xl bg-white shadow-sm flex items-center justify-center flex-shrink-0 text-xl group-hover:scale-110 transition-transform duration-300">
                        {{ suggestion.icon }}
                      </div>
                      <div class="flex-1 min-w-0">
                        <p class="text-base font-semibold text-gray-900 mb-1 group-hover:text-blue-600 transition-colors">{{ suggestion.title }}</p>
                        <p class="text-sm text-gray-500 truncate-2">{{ suggestion.text }}</p>
                      </div>
                    </div>
                  </button>
                </div>
              </div>
            </transition>

            <!-- 消息列表 -->
            <transition-group
              v-if="messages.length > 0"
              tag="div"
              name="list"
              class="space-y-6 pb-36"
            >
              <div
                v-for="(message, index) in messages"
                :key="index"
                class="message-item w-full"
              >
                <!-- 用户消息 -->
                <div v-if="message.role === 'user'" class="flex justify-end mb-6 group">
                  <div class="max-w-[85%] sm:max-w-[75%]">
                    <!-- 编辑模式 -->
                    <div v-if="editingMessageIndex === index" class="bg-gemini-blue-50 rounded-2xl rounded-tr-sm px-4 py-3 shadow-sm border border-blue-200">
                      <textarea
                        v-model="editingMessageContent"
                        class="w-full bg-white border border-gray-200 rounded-lg px-3 py-2 text-gray-800 resize-none focus:outline-none focus:ring-2 focus:ring-blue-400"
                        rows="3"
                        @keydown.enter.ctrl="submitEditedMessage(index)"
                        @keydown.esc="cancelEditMessage"
                      ></textarea>
                      <div class="flex justify-end gap-2 mt-2">
                        <button @click="cancelEditMessage" class="px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">取消</button>
                        <button @click="submitEditedMessage(index)" class="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">重新提问</button>
                      </div>
                    </div>
                    <!-- 显示模式 -->
                    <div v-else class="relative">
                      <div class="bg-gemini-blue-50 text-gray-800 rounded-2xl rounded-tr-sm px-5 py-3.5 shadow-sm border border-blue-100">
                        <p class="leading-relaxed whitespace-pre-wrap">{{ message.content }}</p>
                      </div>
                      <!-- 用户消息操作按钮 -->
                      <div class="flex items-center gap-1 mt-2 justify-end">
                        <!-- 编辑按钮 -->
                        <button
                          @click="startEditMessage(index, message.content)"
                          class="flex items-center gap-1 px-2 py-1 text-xs text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-all opacity-0 group-hover:opacity-100"
                          title="编辑并重新提问"
                        >
                          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"></path>
                          </svg>
                          <span>编辑</span>
                        </button>
                        <!-- 加入记忆按钮 -->
                        <button
                          @click="addToMemory(message.content)"
                          class="flex items-center gap-1 px-2 py-1 text-xs text-gray-400 hover:text-purple-600 hover:bg-purple-50 rounded-lg transition-all opacity-0 group-hover:opacity-100"
                          :class="{ 'text-purple-600 opacity-100': addingMemoryIndex === index }"
                          title="加入长时记忆"
                        >
                          <svg v-if="addingMemoryIndex !== index" class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
                          </svg>
                          <svg v-else class="w-3.5 h-3.5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                          </svg>
                          <span>{{ addingMemoryIndex === index ? '提取中' : '加入记忆' }}</span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- AI 消息 -->
                <div v-else class="flex items-start space-x-3 max-w-full">
                  <div class="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center flex-shrink-0 shadow-sm mt-0.5">
                    <span class="text-white text-xs font-bold">L</span>
                  </div>
                  <div class="flex-1 min-w-0 overflow-hidden">
                    <!-- 思考过程展示 -->
                    <div v-if="message.thinking || message.thinkingSteps?.length > 0 || (loading && index === messages.length - 1 && currentThinkingSteps.length > 0)" class="mb-3">
                      <button
                        @click="toggleThinking(index)"
                        class="flex items-center gap-2 px-3 py-1.5 text-xs rounded-lg transition-colors"
                        :class="loading && index === messages.length - 1 ? 'bg-purple-100 text-purple-700' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
                      >
                        <svg v-if="loading && index === messages.length - 1" class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                        </svg>
                        <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
                        </svg>
                        <span v-if="loading && index === messages.length - 1">
                          思考中（{{ currentThinkingSteps.length }} 步）...
                        </span>
                        <span v-else>
                          查看思考过程（{{ message.thinkingSteps?.length || 0 }} 步）
                        </span>
                        <svg class="w-3 h-3 transition-transform" :class="expandedThinking.includes(index) ? 'rotate-180' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                        </svg>
                      </button>
                      <transition name="expand">
                        <div v-if="expandedThinking.includes(index) || (loading && index === messages.length - 1)" class="mt-2">
                          <div class="thinking-box p-3 rounded-lg border text-sm">
                            <div class="thinking-steps space-y-2">
                              <div
                                v-for="(step, sIdx) in (loading && index === messages.length - 1 ? currentThinkingSteps : message.thinkingSteps || [])"
                                :key="sIdx"
                                class="thinking-step flex items-start gap-2"
                              >
                                <span class="step-number flex-shrink-0 w-5 h-5 rounded-full bg-purple-100 text-purple-600 text-xs flex items-center justify-center font-medium">{{ sIdx + 1 }}</span>
                                <span class="step-content text-gray-600 whitespace-pre-wrap">{{ step }}</span>
                              </div>
                            </div>
                          </div>
                        </div>
                      </transition>
                    </div>
                    <!-- 联网搜索来源展示 - 紧凑标签形式 -->
                    <div v-if="message.webSources && message.webSources.length > 0" class="mb-3">
                      <div class="flex flex-wrap items-center gap-1.5">
                        <span class="text-xs text-gray-500">
                          <svg class="w-3.5 h-3.5 inline mr-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"></path>
                          </svg>
                          网络来源:
                        </span>
                        <!-- 网络来源标签 - 点击打开链接 -->
                        <a
                          v-for="(source, sIdx) in message.webSources"
                          :key="sIdx"
                          :href="source.url"
                          target="_blank"
                          rel="noopener noreferrer"
                          :title="source.title + '\n' + source.url"
                          class="inline-flex items-center gap-1 px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded hover:bg-green-200 transition-colors"
                        >
                          [网络{{ sIdx + 1 }}]
                        </a>
                      </div>
                    </div>
                    <!-- 长时记忆来源展示 -->
                    <div v-if="message.memorySources && message.memorySources.length > 0" class="mb-3">
                      <div class="flex flex-wrap items-center gap-1.5">
                        <span class="text-xs text-gray-500">
                          <svg class="w-3.5 h-3.5 inline mr-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
                          </svg>
                          长时记忆:
                        </span>
                        <!-- 记忆标签 - 点击弹出详情 -->
                        <button
                          v-for="(mem, mIdx) in message.memorySources"
                          :key="mIdx"
                          @click="showSourceDialog(index, 'memory', { ...mem, index: mIdx + 1 })"
                          class="inline-flex items-center gap-1 px-2 py-0.5 text-xs bg-amber-100 text-amber-700 rounded hover:bg-amber-200 transition-colors"
                        >
                          [记忆{{ mIdx + 1 }}]
                        </button>
                      </div>
                    </div>
                    <!-- 知识库引用来源展示 - 紧凑卡片式 -->
                    <!-- 知识库来源展示 - 紧凑标签形式 -->
                    <div v-if="message.sources && (message.sources.chunks?.length > 0 || message.sources.graph_data)" class="mb-3">
                      <div class="flex flex-wrap items-center gap-1.5">
                        <!-- 知识库标签 -->
                        <span class="text-xs text-gray-500">
                          <svg class="w-3.5 h-3.5 inline mr-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
                          </svg>
                          {{ message.sources.kb_name || '知识库' }}:
                        </span>
                        
                        <!-- 图谱数据标签 -->
                        <button
                          v-if="message.sources.graph_data && (message.sources.graph_data.entities?.length > 0 || message.sources.graph_data.relationships?.length > 0)"
                          @click="showSourceDialog(index, 'graph', message.sources.graph_data)"
                          class="inline-flex items-center gap-1 px-2 py-0.5 text-xs bg-indigo-100 text-indigo-700 rounded hover:bg-indigo-200 transition-colors"
                        >
                          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path>
                          </svg>
                          图谱 {{ message.sources.graph_data.entities?.length || 0 }}实体
                        </button>
                        
                        <!-- 文档分片标签 -->
                        <button
                          v-for="(chunk, cIdx) in message.sources.chunks"
                          :key="cIdx"
                          @click="showSourceDialog(index, 'chunk', chunk)"
                          class="inline-flex items-center gap-1 px-2 py-0.5 text-xs bg-purple-100 text-purple-700 rounded hover:bg-purple-200 transition-colors"
                        >
                          [{{ chunk.index }}]
                        </button>
                      </div>
                    </div>
                    
                    <!-- 兼容旧格式的来源数据（数组格式） -->
                    <div v-else-if="message.sources && Array.isArray(message.sources) && message.sources.length > 0" class="mb-3">
                      <div class="flex flex-wrap items-center gap-1.5">
                        <span class="text-xs text-gray-500">
                          <svg class="w-3.5 h-3.5 inline mr-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
                          </svg>
                          来源:
                        </span>
                        <button
                          v-for="(source, sIdx) in message.sources"
                          :key="sIdx"
                          @click="showSourceDialog(index, 'chunk', { index: source.index || sIdx + 1, content: source.content, file_name: source.file_name })"
                          class="inline-flex items-center gap-1 px-2 py-0.5 text-xs bg-purple-100 text-purple-700 rounded hover:bg-purple-200 transition-colors"
                        >
                          [{{ source.index || sIdx + 1 }}]
                        </button>
                      </div>
                    </div>
                    
                    <div class="markdown-gemini prose prose-slate max-w-none" v-html="renderMarkdown(message.content, { sources: { webSources: message.webSources || [], kbSources: Array.isArray(message.sources) ? message.sources : (message.sources?.chunks || []) } })"></div>
                    <!-- 打字光标 -->
                    <span v-if="loading && index === messages.length - 1 && !currentThinking" class="inline-block w-2 h-5 bg-blue-500 ml-1 align-middle animate-pulse"></span>
                    
                    <!-- AI 回复操作按钮 -->
                    <div v-if="!(loading && index === messages.length - 1)" class="flex items-center gap-1 mt-3 pt-3 border-t border-gray-100">
                      <button
                        @click="copyMessageContent(message.content)"
                        class="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                        :class="{ 'text-green-600': copiedMessageIndex === index }"
                        title="复制回复"
                      >
                        <svg v-if="copiedMessageIndex !== index" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                        </svg>
                        <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                        </svg>
                        <span>{{ copiedMessageIndex === index ? '已复制' : '复制' }}</span>
                      </button>
                      
                      <button
                        @click="addToMemory(message.content)"
                        class="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-gray-500 hover:text-purple-600 hover:bg-purple-50 rounded-lg transition-colors"
                        :class="{ 'text-purple-600': addingMemoryIndex === index }"
                        title="加入长时记忆"
                      >
                        <svg v-if="addingMemoryIndex !== index" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
                        </svg>
                        <svg v-else class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                        </svg>
                        <span>{{ addingMemoryIndex === index ? '提取中...' : '加入记忆' }}</span>
                      </button>
                      
                      <button
                        v-if="index === messages.length - 1"
                        @click="regenerateResponse(index)"
                        class="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                        title="重新生成"
                      >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                        </svg>
                        <span>重新生成</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </transition-group>
            

          </div>
        </div>

        <!-- 输入区域 - 悬浮在底部 -->
        <div class="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-white via-white to-transparent pt-10 pb-6 px-4 z-20">
          <div class="max-w-3xl mx-auto">
            <div 
              class="relative bg-gemini-surface rounded-3xl border transition-all duration-300 shadow-gemini-lg"
              :class="isInputFocused ? 'border-blue-400 shadow-xl ring-1 ring-blue-100' : 'border-gemini-border hover:border-gray-300'"
            >
              <div class="flex items-end p-2 pl-4">
                 <!-- 附件按钮 (预留) -->
                <button class="p-2 text-gray-400 hover:text-blue-500 hover:bg-blue-50 rounded-full transition-colors mr-1 mb-1">
                   <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path></svg>
                </button>
                
                <!-- 联网搜索开关 -->
                <div class="relative" ref="webSearchDropdownRef">
                  <button 
                    @click="enableWebSearch = !enableWebSearch"
                    class="p-2 rounded-full transition-colors mr-1 mb-1"
                    :class="enableWebSearch ? 'text-green-600 bg-green-50 hover:bg-green-100' : 'text-gray-400 hover:text-green-500 hover:bg-green-50'"
                    :title="enableWebSearch ? '联网搜索已开启（右键设置）' : '开启联网搜索'"
                    @contextmenu.prevent="showWebSearchSettings = true"
                  >
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"></path>
                    </svg>
                  </button>
                  
                  <!-- 联网搜索设置面板 -->
                  <transition
                    enter-active-class="transition ease-out duration-200"
                    enter-from-class="transform opacity-0 scale-95"
                    enter-to-class="transform opacity-100 scale-100"
                    leave-active-class="transition ease-in duration-75"
                    leave-from-class="transform opacity-100 scale-100"
                    leave-to-class="transform opacity-0 scale-95"
                  >
                    <div
                      v-show="showWebSearchSettings"
                      class="absolute bottom-full left-0 mb-2 w-72 rounded-xl shadow-gemini-xl bg-white ring-1 ring-black ring-opacity-5 focus:outline-none py-3 px-4"
                    >
                      <div class="flex items-center justify-between mb-3">
                        <h3 class="text-sm font-medium text-gray-900">联网搜索设置</h3>
                        <button @click="showWebSearchSettings = false" class="text-gray-400 hover:text-gray-600">
                          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                          </svg>
                        </button>
                      </div>
                      
                      <!-- 超时时间 -->
                      <div class="mb-3">
                        <label class="block text-xs text-gray-600 mb-1">超时时间（秒）</label>
                        <input
                          v-model.number="webSearchConfig.timeout"
                          type="number"
                          min="10"
                          max="300"
                          class="w-full px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-400"
                          placeholder="默认 180"
                        />
                      </div>
                      
                      <!-- 最大结果数 -->
                      <div class="mb-3">
                        <label class="block text-xs text-gray-600 mb-1">每个搜索源最大结果数</label>
                        <input
                          v-model.number="webSearchConfig.max_results"
                          type="number"
                          min="1"
                          max="20"
                          class="w-full px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-400"
                          placeholder="默认 10"
                        />
                      </div>
                      
                      <!-- 搜索源选择 -->
                      <div class="mb-3">
                        <label class="block text-xs text-gray-600 mb-2">搜索源</label>
                        <div class="flex items-center gap-4">
                          <label class="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                            <input
                              v-model="webSearchConfig.use_tavily"
                              type="checkbox"
                              class="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
                            />
                            Tavily
                          </label>
                          <label class="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                            <input
                              v-model="webSearchConfig.use_firecrawl"
                              type="checkbox"
                              class="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500"
                            />
                            Firecrawl
                          </label>
                        </div>
                      </div>
                      
                      <!-- Firecrawl 高级选项 -->
                      <div v-if="webSearchConfig.use_firecrawl" class="space-y-2">
                        <label class="block text-xs text-gray-600 mb-1">Firecrawl 模式</label>
                        <label class="flex items-start gap-2 text-sm text-gray-700 cursor-pointer">
                          <input
                            v-model="webSearchConfig.firecrawl_scrape_content"
                            type="checkbox"
                            class="w-4 h-4 mt-0.5 text-green-600 border-gray-300 rounded focus:ring-green-500"
                          />
                          <div>
                            <span>抓取页面内容</span>
                            <p class="text-xs text-gray-400 mt-0.5">关闭：只获取搜索摘要，速度快</p>
                            <p class="text-xs text-gray-400">开启：访问网页读取全文，更详细但更慢</p>
                          </div>
                        </label>
                      </div>
                      
                      <!-- 保存按钮 -->
                      <button
                        @click="saveWebSearchConfig"
                        class="w-full py-1.5 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                      >
                        保存设置
                      </button>
                    </div>
                  </transition>
                </div>

                <!-- 文本输入 -->
                <textarea
                  ref="inputTextarea"
                  v-model="inputMessage"
                  @keydown.enter.exact.prevent="handleSend"
                  @input="adjustTextareaHeight"
                  @focus="isInputFocused = true"
                  @blur="isInputFocused = false"
                  placeholder="输入消息，或者上传图片..."
                  class="flex-1 bg-transparent border-0 focus:ring-0 text-gray-800 placeholder-gray-400 resize-none max-h-48 py-3 px-2 scrollbar-hide text-base leading-relaxed"
                  rows="1"
                  :disabled="loading"
                ></textarea>

                <!-- 发送/停止按钮 -->
                <div class="flex items-center pb-1 pl-2">
                   <!-- 停止按钮（流式生成时） -->
                   <button
                    v-if="loading"
                    @click="stopGeneration"
                    class="p-2.5 rounded-full bg-red-500 text-white shadow-lg hover:bg-red-600 transition-all duration-300 transform hover:scale-105 active:scale-95"
                    title="停止生成"
                  >
                    <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                      <rect x="6" y="6" width="12" height="12" rx="2"></rect>
                    </svg>
                  </button>
                   <!-- 发送按钮 -->
                   <button
                    v-else
                    @click="handleSend"
                    class="p-2.5 rounded-full transition-all duration-300 transform"
                    :class="canSend ? 'bg-blue-600 text-white shadow-lg hover:bg-blue-700 hover:scale-105 active:scale-95' : 'bg-gray-100 text-gray-400 cursor-not-allowed'"
                    :disabled="!canSend"
                  >
                    <svg class="w-5 h-5 transform rotate-90" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
            
            <div class="flex justify-between items-center mt-3 px-2">
               <!-- 底部工具栏 -->
               <div class="flex items-center space-x-4">
                  <!-- 知识库选择 -->
                  <div class="relative" ref="kbDropdownRef">
                    <button
                      @click="showKbDropdown = !showKbDropdown"
                      class="flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs transition-all duration-200"
                      :class="selectedKnowledgeBase ? 'bg-blue-50 text-blue-600 hover:bg-blue-100' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
                      </svg>
                      <span>{{ selectedKnowledgeBase ? selectedKnowledgeBase.name : '选择知识库' }}</span>
                      <svg class="w-3 h-3 transition-transform" :class="showKbDropdown ? 'rotate-180' : ''" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                      </svg>
                    </button>
                    
                    <!-- 知识库下拉菜单 -->
                    <transition
                      enter-active-class="transition ease-out duration-200"
                      enter-from-class="transform opacity-0 scale-95"
                      enter-to-class="transform opacity-100 scale-100"
                      leave-active-class="transition ease-in duration-75"
                      leave-from-class="transform opacity-100 scale-100"
                      leave-to-class="transform opacity-0 scale-95"
                    >
                      <div
                        v-show="showKbDropdown"
                        class="absolute bottom-full left-0 mb-2 w-64 rounded-xl shadow-gemini-xl bg-white ring-1 ring-black ring-opacity-5 focus:outline-none py-2 max-h-64 overflow-y-auto scrollbar-gemini"
                      >
                        <button
                          @click="selectKnowledgeBase(null)"
                          class="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 transition-colors flex items-center"
                          :class="!selectedKnowledgeBase ? 'bg-blue-50 text-blue-600' : 'text-gray-700'"
                        >
                          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                          </svg>
                          不使用知识库
                        </button>
                        <div class="border-t border-gray-100 my-1"></div>
                        <button
                          v-for="kb in knowledgeBases"
                          :key="kb.id"
                          @click="selectKnowledgeBase(kb)"
                          class="w-full px-4 py-2 text-left text-sm hover:bg-gray-50 transition-colors flex items-center justify-between"
                          :class="selectedKnowledgeBase?.id === kb.id ? 'bg-blue-50 text-blue-600' : 'text-gray-700'"
                        >
                          <div class="flex items-center min-w-0 flex-1">
                            <svg class="w-4 h-4 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"></path>
                            </svg>
                            <span class="truncate">{{ kb.name }}</span>
                          </div>
                          <svg v-if="selectedKnowledgeBase?.id === kb.id" class="w-4 h-4 flex-shrink-0 ml-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
                          </svg>
                        </button>
                        <div v-if="knowledgeBases.length === 0" class="px-4 py-3 text-sm text-gray-500 text-center">
                          暂无知识库
                        </div>
                      </div>
                    </transition>
                  </div>
                  
                  <!-- 模型选择器 -->
                  <ModelSelector 
                    :config="llmConfig" 
                    @update:config="handleLLMConfigUpdate"
                  />
                  
                  <!-- 上下文设置按钮 -->
                  <div class="relative">
                    <button
                      @click="showContextSettings = !showContextSettings"
                      class="p-2 rounded-full transition-colors text-gray-400 hover:text-blue-500 hover:bg-blue-50"
                      title="上下文设置"
                    >
                      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                      </svg>
                    </button>
                    
                    <!-- 上下文设置面板 -->
                    <transition
                      enter-active-class="transition ease-out duration-200"
                      enter-from-class="transform opacity-0 scale-95"
                      enter-to-class="transform opacity-100 scale-100"
                      leave-active-class="transition ease-in duration-75"
                      leave-from-class="transform opacity-100 scale-100"
                      leave-to-class="transform opacity-0 scale-95"
                    >
                      <div
                        v-show="showContextSettings"
                        class="absolute bottom-full right-0 mb-2 w-72 rounded-xl shadow-gemini-xl bg-white ring-1 ring-black ring-opacity-5 focus:outline-none py-3 px-4"
                      >
                        <div class="flex items-center justify-between mb-3">
                          <h3 class="text-sm font-medium text-gray-900">上下文设置</h3>
                          <button @click="showContextSettings = false" class="text-gray-400 hover:text-gray-600">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                            </svg>
                          </button>
                        </div>
                        
                        <div class="space-y-3">
                          <div>
                            <label class="block text-xs text-gray-600 mb-1">最大上下文 Token 数</label>
                            <input
                              v-model.number="contextConfig.max_context_tokens"
                              type="number"
                              min="1000"
                              step="1000"
                              class="w-full px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                              placeholder="16000"
                            />
                            <p class="text-xs text-gray-400 mt-1">超过此限制时，旧消息会被自动压缩</p>
                          </div>
                          
                          <!-- 快捷选项 -->
                          <div class="flex flex-wrap gap-2">
                            <button
                              v-for="preset in [4000, 8000, 16000, 32000]"
                              :key="preset"
                              @click="contextConfig.max_context_tokens = preset"
                              class="px-2 py-1 text-xs rounded-md transition-colors"
                              :class="contextConfig.max_context_tokens === preset ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
                            >
                              {{ preset / 1000 }}K
                            </button>
                          </div>
                        </div>
                        
                        <!-- 保存按钮 -->
                        <button
                          @click="saveContextConfig"
                          class="w-full mt-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                        >
                          保存设置
                        </button>
                      </div>
                    </transition>
                  </div>
               </div>
               
               <p class="text-xs text-gray-400 text-center">
                 LiuYun 可能会产生不准确的信息，请核实。
               </p>
            </div>
          </div>
        </div>
      </main>
    </div>
    
    <!-- 来源详情对话框 -->
    <el-dialog
      v-model="sourceDialogVisible"
      :title="sourceDialogTitle"
      width="650px"
      :close-on-click-modal="true"
      class="source-dialog"
    >
      <!-- 图谱数据内容 -->
      <div v-if="sourceDialogType === 'graph'" class="space-y-4 max-h-[70vh] overflow-y-auto">
        <!-- 实体列表 -->
        <div v-if="sourceDialogData?.entities?.length > 0">
          <div class="text-sm font-medium text-indigo-600 mb-2 sticky top-0 bg-white py-1">
            <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path>
            </svg>
            实体 ({{ sourceDialogData.entities.length }})
          </div>
          <div class="space-y-2">
            <div
              v-for="(entity, eIdx) in sourceDialogData.entities"
              :key="eIdx"
              class="px-3 py-2 bg-indigo-50 rounded-lg border border-indigo-200"
            >
              <div class="flex items-center gap-2 mb-1">
                <span class="font-medium text-indigo-700">{{ entity.name }}</span>
                <span v-if="entity.type" class="text-xs px-1.5 py-0.5 bg-indigo-100 text-indigo-600 rounded">{{ entity.type }}</span>
              </div>
              <div v-if="entity.description" class="text-xs text-gray-600 leading-relaxed">
                <!-- 处理 <SEP> 分隔的多个描述，只显示第一个 -->
                {{ formatEntityDescription(entity.description) }}
              </div>
            </div>
          </div>
        </div>
        <!-- 关系列表 -->
        <div v-if="sourceDialogData?.relationships?.length > 0">
          <div class="text-sm font-medium text-indigo-600 mb-2 sticky top-0 bg-white py-1">
            <svg class="w-4 h-4 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path>
            </svg>
            关系 ({{ sourceDialogData.relationships.length }})
          </div>
          <div class="space-y-2">
            <div
              v-for="(rel, rIdx) in sourceDialogData.relationships"
              :key="rIdx"
              class="px-3 py-2 bg-gray-50 rounded-lg border border-gray-200 text-sm"
            >
              <div class="flex items-center flex-wrap gap-1">
                <span class="px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded text-xs font-medium">{{ rel.source }}</span>
                <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"></path>
                </svg>
                <span class="px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded text-xs font-medium">{{ rel.target }}</span>
              </div>
              <div v-if="rel.description" class="text-xs text-gray-500 mt-1.5 leading-relaxed">{{ formatEntityDescription(rel.description) }}</div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 文档分片内容 -->
      <div v-else-if="sourceDialogType === 'chunk'" class="space-y-3">
        <div v-if="sourceDialogData?.file_name" class="text-sm text-gray-500 flex items-center gap-1">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
          </svg>
          {{ sourceDialogData.file_name }}
        </div>
        <div class="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap bg-gray-50 p-4 rounded-lg border max-h-[60vh] overflow-y-auto">{{ sourceDialogData?.content }}</div>
      </div>
      
      <!-- 长时记忆内容 -->
      <div v-else-if="sourceDialogType === 'memory'" class="space-y-3">
        <div class="flex items-center gap-2">
          <span class="px-2 py-1 text-xs rounded-full bg-amber-100 text-amber-700">
            {{ getMemoryCategoryLabel(sourceDialogData?.category) }}
          </span>
        </div>
        <div class="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap bg-amber-50 p-4 rounded-lg border border-amber-200 max-h-[60vh] overflow-y-auto">{{ sourceDialogData?.content }}</div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getConversations, getConversation, updateConversation, deleteConversation } from '@/api/chat'
import { getKnowledgeBases } from '@/api/knowledge'
import { getProviders, getModels, getModelGroup } from '@/api/llm'
import { autoExtractMemory, createMemory } from '@/api/memory'
import { renderMarkdown } from '@/utils/markdown'
import { ElMessageBox, ElMessage } from 'element-plus'
import ModelSelector from '@/components/chat/ModelSelector.vue'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const router = useRouter()
const authStore = useAuthStore()

// 状态
const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const currentConversationId = ref(null)
const currentConversationTitle = ref('')
const showSidebar = ref(true)  // 默认显示侧边栏
const showUserMenu = ref(false)
const showKbDropdown = ref(false)
const conversations = ref([])
const knowledgeBases = ref([])
const selectedKnowledgeBase = ref(null)
const isInputFocused = ref(false)
const editingConvId = ref(null)
const editingTitle = ref('')
const sidebarWidth = ref(288)  // 默认宽度 288px (w-72)
const isResizing = ref(false)
const editingMessageIndex = ref(null)
const editingMessageContent = ref('')
const expandedSources = ref([])
const expandedSourceItems = ref({})  // 存储每个消息中展开的来源项 { messageIndex: [sourceIndex1, sourceIndex2] }
const expandedGraphData = ref([])  // 存储展开图谱数据的消息索引
const expandedThinking = ref([])
const currentThinking = ref('')
const currentThinkingSteps = ref([])
const enableWebSearch = ref(false)
const isSearching = ref(false)
const showWebSearchSettings = ref(false)
const webSearchDropdownRef = ref(null)
const copiedMessageIndex = ref(null)
const addingMemoryIndex = ref(null)
const webSearchConfig = ref({
  timeout: null,
  max_results: null,
  use_tavily: true,
  use_firecrawl: true,
  firecrawl_scrape_content: false  // Firecrawl 是否抓取页面内容
})
let abortController = null

// 上下文设置
const showContextSettings = ref(false)
const contextConfig = ref({
  max_context_tokens: 16000  // 默认 16k
})

// 来源详情对话框
const sourceDialogVisible = ref(false)
const sourceDialogType = ref('')  // 'graph' | 'chunk' | 'memory'
const sourceDialogData = ref(null)
const sourceDialogTitle = computed(() => {
  if (sourceDialogType.value === 'graph') return '知识图谱数据'
  if (sourceDialogType.value === 'chunk') return `来源 [${sourceDialogData.value?.index || ''}]`
  if (sourceDialogType.value === 'memory') return `记忆 [${sourceDialogData.value?.index || ''}] - ${sourceDialogData.value?.title || ''}`
  return '来源详情'
})

// LLM 配置
const llmConfig = ref({
  provider: '302ai',
  model: 'claude-sonnet-4-5-20250929',
  apiKey: null,
  baseUrl: null,
  configId: null
})

// 更新 LLM 配置
const handleLLMConfigUpdate = (config) => {
  console.log('[LLM Config Update]', config)
  llmConfig.value = config
  // 保存到 localStorage
  localStorage.setItem('llm_config', JSON.stringify(config))
  console.log('[LLM Config Saved]', llmConfig.value)
}

// 加载保存的 LLM 配置
const loadLLMConfig = () => {
  const saved = localStorage.getItem('llm_config')
  if (saved) {
    try {
      llmConfig.value = JSON.parse(saved)
    } catch (e) {
      console.error('Failed to load LLM config:', e)
    }
  }
}

// 加载上下文配置
const loadContextConfig = () => {
  const saved = localStorage.getItem('context_config')
  if (saved) {
    try {
      contextConfig.value = JSON.parse(saved)
    } catch (e) {
      console.error('Failed to load context config:', e)
    }
  }
}

// 保存上下文配置
const saveContextConfig = () => {
  localStorage.setItem('context_config', JSON.stringify(contextConfig.value))
  showContextSettings.value = false
  ElMessage.success('上下文设置已保存')
}

// Refs
const inputTextarea = ref(null)
const userMenuRef = ref(null)
const kbDropdownRef = ref(null)
const chatContainer = ref(null)
let titleInput = null

// 计算属性
const canSend = computed(() => inputMessage.value.trim() && !loading.value)
const userInitial = computed(() => authStore.user?.username?.charAt(0).toUpperCase() || 'U')

// 建议问题
const suggestions = ref([
  {
    icon: '💡',
    title: '创意灵感',
    text: '帮我想一个有创意的项目名称'
  },
  {
    icon: '📝',
    title: '写作助手',
    text: '帮我写一篇关于人工智能的文章'
  },
  {
    icon: '🔍',
    title: '知识问答',
    text: '解释一下量子计算的基本原理'
  },
  {
    icon: '💻',
    title: '编程帮助',
    text: '用 Python 写一个快速排序算法'
  },
])

// 方法
const toggleSidebar = () => {
  showSidebar.value = !showSidebar.value
}

const toggleUserMenu = () => {
  showUserMenu.value = !showUserMenu.value
}

const handleNewChat = () => {
  messages.value = []
  currentConversationId.value = null
  currentConversationTitle.value = ''
  inputMessage.value = ''
  // Focus input
  nextTick(() => {
    inputTextarea.value?.focus()
  })
}

const handleSuggestion = (text) => {
  inputMessage.value = text
  handleSend()
}

const adjustTextareaHeight = () => {
  nextTick(() => {
    if (inputTextarea.value) {
      inputTextarea.value.style.height = 'auto'
      const scrollHeight = inputTextarea.value.scrollHeight
      inputTextarea.value.style.height = Math.min(scrollHeight, 192) + 'px' // max-h-48 = 12rem = 192px
    }
  })
}

// 用户是否手动滚动（用于控制流式回答时是否自动滚动）
const userHasScrolled = ref(false)

const scrollToBottom = (force = false) => {
  nextTick(() => {
    if (chatContainer.value) {
      // 如果用户手动滚动了且不是强制滚动，则不自动滚动
      if (userHasScrolled.value && !force) {
        return
      }
      chatContainer.value.scrollTo({
        top: chatContainer.value.scrollHeight,
        behavior: 'smooth'
      })
    }
  })
}

// 检测用户是否手动滚动
const handleChatScroll = () => {
  if (!chatContainer.value || !loading.value) {
    return
  }
  const { scrollTop, scrollHeight, clientHeight } = chatContainer.value
  // 如果距离底部超过 100px，认为用户手动滚动了
  const distanceFromBottom = scrollHeight - scrollTop - clientHeight
  userHasScrolled.value = distanceFromBottom > 100
}

const handleSend = async () => {
  if (!canSend.value) return

  const userMessage = inputMessage.value.trim()
  inputMessage.value = ''
  adjustTextareaHeight()

  // 重置用户滚动状态，发送新消息时自动滚动到底部
  userHasScrolled.value = false

  // 添加用户消息
  messages.value.push({
    role: 'user',
    content: userMessage,
  })

  scrollToBottom(true)

  try {
    // 默认使用流式响应
    await handleStreamMode(userMessage)
  } catch (error) {
    console.error('Chat error:', error)
    messages.value.push({
      role: 'assistant',
      content: `抱歉，发生了错误：${error.message || '未知错误'}`,
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

const handleStreamMode = async (userMessage) => {
  const messageIndex = messages.value.length
  messages.value.push({
    role: 'assistant',
    content: '',
    sources: [],
    webSources: [],
    memorySources: [],
    thinking: false,
    thinkingSteps: []
  })
  
  loading.value = true
  isSearching.value = false
  abortController = new AbortController()
  currentThinking.value = ''
  currentThinkingSteps.value = []
  let conversationId = currentConversationId.value
  let finalMessage = userMessage
  let sources = []

  try {
    // 思考步骤由后端统一发送，前端只负责接收和显示
    
    // 保存思考步骤到消息
    messages.value[messageIndex].thinking = true
    messages.value[messageIndex].thinkingSteps = [...currentThinkingSteps.value]
    
    // 开始生成回答
    currentThinking.value = '生成回答中'
    
    await sendMessageStreamWithAbort(
      {
        message: finalMessage,
        conversation_id: conversationId,
      },
      abortController.signal,
      (content, newConversationId, webSources, kbSources, memorySources) => {
        if (newConversationId) {
          conversationId = newConversationId
          if (!currentConversationId.value) {
            currentConversationId.value = newConversationId
            generateTitle(newConversationId, userMessage)
            fetchConversations()
          }
        }
        
        if (webSources && webSources.length > 0) {
          // 保存联网搜索来源
          messages.value[messageIndex].webSources = webSources
        }
        
        // 【立即显示知识库来源】收到 kb_sources 事件时立即更新
        if (kbSources) {
          console.log('[KB Sources] Received kb_sources, updating message:', kbSources)
          messages.value[messageIndex].sources = kbSources
        }
        
        // 【立即显示长时记忆来源】收到 memory_sources 事件时立即更新
        if (memorySources && memorySources.length > 0) {
          console.log('[Memory Sources] Received memory_sources, updating message:', memorySources)
          messages.value[messageIndex].memorySources = memorySources
        }
        
        if (content) {
          // 清除当前思考状态，开始显示内容
          currentThinking.value = ''
          messages.value[messageIndex].content += content
          scrollToBottom()
        }
      },
      (kbSources) => {
        console.log('Stream completed, kb sources:', kbSources)
        // 保存知识库来源（仅当还没有设置时，作为备用）
        if (kbSources && (kbSources.chunks?.length > 0 || kbSources.graph_data) && !messages.value[messageIndex].sources) {
          messages.value[messageIndex].sources = kbSources
        }
        // 保存思考步骤到消息
        if (currentThinkingSteps.value.length > 0) {
          messages.value[messageIndex].thinking = true
          messages.value[messageIndex].thinkingSteps = [...currentThinkingSteps.value]
        }
        loading.value = false
        isSearching.value = false
        abortController = null
        currentThinking.value = ''
        currentThinkingSteps.value = []
      },
      (error) => {
        if (error !== 'aborted') {
          messages.value[messageIndex].content += `\n\n⚠️ ${error}`
        }
        loading.value = false
        isSearching.value = false
        abortController = null
        currentThinking.value = ''
        currentThinkingSteps.value = []
      }
    )
  } catch (e) {
    loading.value = false
    isSearching.value = false
    abortController = null
    currentThinking.value = ''
    currentThinkingSteps.value = []
    if (e.name !== 'AbortError') {
      throw e
    }
  }
}

// 添加思考步骤
const addThinkingStep = (step) => {
  currentThinkingSteps.value.push(step)
  currentThinking.value = ''
}

// 支持中断的流式请求
const sendMessageStreamWithAbort = async (data, signal, onMessage, onDone, onError) => {
  try {
    // 使用新的 LLM API，支持模型切换
    const requestData = {
      message: data.message,
      conversation_id: data.conversation_id,
      stream: true,
      provider: llmConfig.value.provider,
      model: llmConfig.value.model,
      api_key: llmConfig.value.apiKey,
      base_url: llmConfig.value.baseUrl,
      config_id: llmConfig.value.configId,
      knowledge_base_id: selectedKnowledgeBase.value?.id ? String(selectedKnowledgeBase.value.id) : null,
      enable_web_search: enableWebSearch.value,
      web_search_config: enableWebSearch.value ? {
        timeout: webSearchConfig.value.timeout || null,
        max_results: webSearchConfig.value.max_results || null,
        use_tavily: webSearchConfig.value.use_tavily,
        use_firecrawl: webSearchConfig.value.use_firecrawl,
        firecrawl_scrape_content: webSearchConfig.value.firecrawl_scrape_content
      } : null
    }
    
    // 调试日志
    console.log('[LLM Request]', {
      provider: requestData.provider,
      model: requestData.model,
      hasApiKey: !!requestData.api_key,
      baseUrl: requestData.base_url,
      configId: requestData.config_id,
      knowledge_base_id: requestData.knowledge_base_id,
      enable_web_search: requestData.enable_web_search
    })
    console.log('[Web Search] enableWebSearch.value =', enableWebSearch.value)
    console.log('[Knowledge Base] selectedKnowledgeBase =', selectedKnowledgeBase.value)
    
    const response = await fetch('/api/llm/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
      body: JSON.stringify(requestData),
      signal
    })

    if (!response.ok) {
      throw new Error('Network response was not ok')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''

      for (const rawEvent of parts) {
        const lines = rawEvent.split('\n')
        const dataLines = []

        for (const line of lines) {
          if (line.startsWith('data:')) {
            dataLines.push(line.replace(/^data:\s?/, ''))
          }
        }

        if (dataLines.length === 0) continue

        const payload = dataLines.join('\n').trim()

        if (payload === '[DONE]') {
          onDone?.()
          continue
        }

        try {
          const parsed = JSON.parse(payload)

          console.log('[Stream Event]', parsed)
          
          if (parsed.error) {
            console.log('[Stream] Error:', parsed.error)
            onError?.(parsed.error)
          } else if (parsed.type === 'thinking_step') {
            // 思考步骤事件
            console.log('[Stream] Thinking step:', parsed.step)
            if (parsed.step) {
              addThinkingStep(parsed.step)
            }
          } else if (parsed.type === 'search_start') {
            // 搜索开始事件
            console.log('[Stream] Search started')
            isSearching.value = true
          } else if (parsed.type === 'search_complete') {
            // 搜索完成事件，保存来源
            console.log('[Stream] Search complete, sources:', parsed.sources)
            isSearching.value = false
            if (parsed.sources && parsed.sources.length > 0) {
              onMessage?.('', null, parsed.sources)
            }
          } else if (parsed.type === 'kb_sources') {
            // 知识库来源事件 - 立即显示
            console.log('[Stream] KB sources:', parsed.sources)
            if (parsed.sources) {
              onMessage?.('', null, null, parsed.sources)
            }
          } else if (parsed.type === 'memory_sources') {
            // 长时记忆来源事件
            console.log('[Stream] Memory sources:', parsed.memories)
            if (parsed.memories && parsed.memories.length > 0) {
              onMessage?.('', null, null, null, parsed.memories)
            }
          } else if (parsed.type === 'search_error') {
            // 搜索错误事件
            console.log('[Stream] Search error:', parsed.error)
            isSearching.value = false
            console.warn('Web search error:', parsed.error)
          } else if (parsed.type === 'content') {
            // 内容事件
            onMessage?.(parsed.content)
          } else if (parsed.type === 'done') {
            // 完成事件
            console.log('[Stream] Done', parsed)
            // 传递知识库来源信息
            onDone?.(parsed.sources || [])
          } else if (parsed.type === 'error') {
            console.log('[Stream] Error event:', parsed.error)
            onError?.(parsed.error)
          } else if (parsed.conversation_id) {
            console.log('[Stream] Conversation ID:', parsed.conversation_id)
            onMessage?.('', parsed.conversation_id)
          } else if (parsed.content !== undefined && parsed.content !== null) {
            onMessage?.(parsed.content)
          }
        } catch (e) {
          // 忽略解析失败
        }
      }
    }
    
    onDone?.()
  } catch (error) {
    if (error.name === 'AbortError') {
      onError?.('aborted')
    } else {
      onError?.(error.message)
    }
  }
}

const fetchConversations = async () => {
  try {
    const res = await getConversations({ limit: 20 })
    conversations.value = res
  } catch (error) {
    console.error('Failed to fetch conversations:', error)
  }
}

const fetchKnowledgeBases = async () => {
  try {
    const res = await getKnowledgeBases()
    knowledgeBases.value = res
  } catch (error) {
    console.error('Failed to fetch knowledge bases:', error)
  }
}

const selectKnowledgeBase = (kb) => {
  selectedKnowledgeBase.value = kb
  showKbDropdown.value = false
}

// 编辑对话标题
const startEdit = (conv) => {
  editingConvId.value = conv.id
  editingTitle.value = conv.title || '新对话'
  nextTick(() => {
    if (titleInput) {
      titleInput.focus()
      titleInput.select()
    }
  })
}

const cancelEdit = () => {
  editingConvId.value = null
  editingTitle.value = ''
}

// 删除对话
const confirmDeleteConversation = async (conv) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除对话"${conv.title || '新对话'}"吗？`,
      '删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await deleteConversation(conv.id)
    
    // 从列表中移除
    conversations.value = conversations.value.filter(c => c.id !== conv.id)
    
    // 如果删除的是当前对话，清空聊天区域
    if (currentConversationId.value === conv.id) {
      handleNewChat()
    }
    
    ElMessage.success('删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete conversation:', error)
      ElMessage.error('删除失败，请重试')
    }
  }
}

const saveTitle = async (convId) => {
  if (!editingTitle.value.trim()) {
    cancelEdit()
    return
  }
  
  try {
    await updateConversation(convId, { title: editingTitle.value.trim() })
    
    // 更新本地列表
    const conv = conversations.value.find(c => c.id === convId)
    if (conv) {
      conv.title = editingTitle.value.trim()
    }
    
    // 如果是当前对话，也更新标题
    if (currentConversationId.value === convId) {
      currentConversationTitle.value = editingTitle.value.trim()
    }
    
    cancelEdit()
  } catch (error) {
    console.error('Failed to update title:', error)
    cancelEdit()
  }
}

// 自动生成对话标题
const generateTitle = async (convId, firstMessage) => {
  // 使用第一条消息的前20个字符作为标题
  const title = firstMessage.length > 20 
    ? firstMessage.substring(0, 20) + '...' 
    : firstMessage
  
  try {
    await updateConversation(convId, { title })
    
    // 更新本地列表
    const conv = conversations.value.find(c => c.id === convId)
    if (conv) {
      conv.title = title
    }
    
    // 更新当前对话标题
    if (currentConversationId.value === convId) {
      currentConversationTitle.value = title
    }
  } catch (error) {
    console.error('Failed to generate title:', error)
  }
}

const loadConversation = async (id) => {
  if (currentConversationId.value === id) return
  
  try {
    loading.value = true
    const res = await getConversation(id)
    currentConversationId.value = res.id
    currentConversationTitle.value = res.title
    messages.value = res.messages.map(msg => ({
      role: msg.role,
      // 过滤掉知识库上下文前缀，只显示用户原始问题
      content: msg.role === 'user' ? extractUserQuestion(msg.content) : msg.content,
      // 恢复元数据（webSources, sources, memorySources, thinkingSteps 等）
      webSources: msg.metadata?.web_sources || [],
      sources: msg.metadata?.sources || [],
      memorySources: msg.metadata?.memory_sources || [],
      thinking: msg.metadata?.thinking_steps?.length > 0,
      thinkingSteps: msg.metadata?.thinking_steps || []
    }))
    
    // 在移动端加载后自动关闭侧边栏
    if (window.innerWidth < 768) {
      showSidebar.value = false
    }
    
    // 加载对话时重置滚动状态并强制滚动到底部
    userHasScrolled.value = false
    scrollToBottom(true)
  } catch (error) {
    console.error('Failed to load conversation:', error)
  } finally {
    loading.value = false
  }
}

const formatDate = (date) => {
  if (!date) return ''
  return dayjs(date).fromNow()
}

// 从消息中提取用户原始问题（过滤掉知识库上下文）
const extractUserQuestion = (content) => {
  if (!content) return ''
  
  // 匹配 "用户问题：xxx" 模式
  const userQuestionMatch = content.match(/用户问题：(.+)$/s)
  if (userQuestionMatch) {
    return userQuestionMatch[1].trim()
  }
  
  // 如果没有匹配到，返回原始内容
  return content
}

const handleLogout = async () => {
  showUserMenu.value = false
  await authStore.logout()
  router.push('/login')
}

const goToAdminUsers = () => {
  showUserMenu.value = false
  router.push('/admin/users')
}

// 编辑用户消息
const startEditMessage = (index, content) => {
  editingMessageIndex.value = index
  editingMessageContent.value = content
}

const cancelEditMessage = () => {
  editingMessageIndex.value = null
  editingMessageContent.value = ''
}

const submitEditedMessage = async (index) => {
  const newContent = editingMessageContent.value.trim()
  if (!newContent) return
  
  // 删除该消息及之后的所有消息
  messages.value = messages.value.slice(0, index)
  
  // 重置编辑状态
  cancelEditMessage()
  
  // 重新发送消息
  inputMessage.value = newContent
  await handleSend()
}

// 复制消息内容
const copyMessageContent = async (content) => {
  try {
    await navigator.clipboard.writeText(content)
    // 找到当前消息的索引
    const index = messages.value.findIndex(m => m.content === content && m.role === 'assistant')
    copiedMessageIndex.value = index
    
    // 2秒后重置状态
    setTimeout(() => {
      copiedMessageIndex.value = null
    }, 2000)
  } catch (err) {
    console.error('复制失败:', err)
  }
}

// 加入长时记忆
const addToMemory = async (content) => {
  if (addingMemoryIndex.value !== null) return
  
  // 找到当前消息的索引
  const index = messages.value.findIndex(m => m.content === content)
  addingMemoryIndex.value = index
  
  try {
    // 调用AI自动提取
    const extracted = await autoExtractMemory(content)
    
    // 直接创建记忆，不需要用户确认
    await createMemory({
      title: extracted.title,
      content: extracted.content,
      category: extracted.category,
      priority: extracted.priority,
      is_active: true
    })
    
    ElMessage.success(`已添加到长时记忆: ${extracted.title}`)
  } catch (err) {
    console.error('添加记忆失败:', err)
    ElMessage.error('添加失败，请重试')
  } finally {
    addingMemoryIndex.value = null
  }
}

// 获取分类标签
const getCategoryLabel = (category) => {
  const labels = {
    general: '通用',
    preference: '偏好',
    fact: '事实',
    instruction: '指令'
  }
  return labels[category] || category
}

// 获取记忆分类标签（用于模板）
const getMemoryCategoryLabel = (category) => {
  return getCategoryLabel(category)
}

// 重新生成回复
const regenerateResponse = async (index) => {
  if (loading.value) return
  
  // 找到对应的用户消息（AI 回复的前一条）
  const userMessageIndex = index - 1
  if (userMessageIndex < 0 || messages.value[userMessageIndex]?.role !== 'user') {
    console.error('找不到对应的用户消息')
    return
  }
  
  const userMessage = messages.value[userMessageIndex].content
  
  // 删除当前 AI 回复
  messages.value = messages.value.slice(0, index)
  
  // 重新发送
  inputMessage.value = userMessage
  await handleSend()
}

// 停止生成
const stopGeneration = () => {
  if (abortController) {
    abortController.abort()
    abortController = null
  }
  loading.value = false
}

// 切换引用来源展开/收起
const toggleSources = (index) => {
  const idx = expandedSources.value.indexOf(index)
  if (idx > -1) {
    expandedSources.value.splice(idx, 1)
  } else {
    expandedSources.value.push(index)
  }
}

// 切换单个来源项展开/收起
const toggleSourceItem = (messageIndex, sourceIndex) => {
  if (!expandedSourceItems.value[messageIndex]) {
    expandedSourceItems.value[messageIndex] = []
  }
  const items = expandedSourceItems.value[messageIndex]
  const idx = items.indexOf(sourceIndex)
  if (idx > -1) {
    items.splice(idx, 1)
  } else {
    items.push(sourceIndex)
  }
}

// 检查来源项是否展开
const isSourceItemExpanded = (messageIndex, sourceIndex) => {
  return expandedSourceItems.value[messageIndex]?.includes(sourceIndex) || false
}

// 切换图谱数据展开/收起
const toggleGraphData = (index) => {
  const idx = expandedGraphData.value.indexOf(index)
  if (idx > -1) {
    expandedGraphData.value.splice(idx, 1)
  } else {
    expandedGraphData.value.push(index)
  }
}

// 检查图谱数据是否展开
const isGraphDataExpanded = (index) => {
  return expandedGraphData.value.includes(index)
}

// 显示来源详情对话框
const showSourceDialog = (messageIndex, type, data) => {
  sourceDialogType.value = type
  sourceDialogData.value = data
  sourceDialogVisible.value = true
}

// 格式化实体描述（处理 <SEP> 分隔的多个描述，只取第一个并限制长度）
const formatEntityDescription = (description) => {
  if (!description) return ''
  // 按 <SEP> 分割，取第一个描述
  const firstDesc = description.split('<SEP>')[0].trim()
  // 限制长度
  if (firstDesc.length > 150) {
    return firstDesc.slice(0, 150) + '...'
  }
  return firstDesc
}

// 保存联网搜索配置
const saveWebSearchConfig = () => {
  localStorage.setItem('web_search_config', JSON.stringify(webSearchConfig.value))
  showWebSearchSettings.value = false
  console.log('[Web Search Config] Saved:', webSearchConfig.value)
}

// 加载联网搜索配置
const loadWebSearchConfig = () => {
  const saved = localStorage.getItem('web_search_config')
  if (saved) {
    try {
      webSearchConfig.value = JSON.parse(saved)
    } catch (e) {
      console.error('Failed to load web search config:', e)
    }
  }
}

// 切换思考过程展开/收起
const toggleThinking = (index) => {
  const idx = expandedThinking.value.indexOf(index)
  if (idx > -1) {
    expandedThinking.value.splice(idx, 1)
  } else {
    expandedThinking.value.push(index)
  }
}

// 侧边栏拖拽调整宽度
const startResize = (e) => {
  isResizing.value = true
  const startX = e.clientX
  const startWidth = sidebarWidth.value

  const handleMouseMove = (e) => {
    if (!isResizing.value) return
    
    const deltaX = e.clientX - startX
    const newWidth = startWidth + deltaX
    
    // 限制宽度范围：最小 200px，最大 500px
    if (newWidth >= 200 && newWidth <= 500) {
      sidebarWidth.value = newWidth
    }
  }

  const handleMouseUp = () => {
    isResizing.value = false
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  }

  document.addEventListener('mousemove', handleMouseMove)
  document.addEventListener('mouseup', handleMouseUp)
  document.body.style.cursor = 'ew-resize'
  document.body.style.userSelect = 'none'
}

// 点击外部关闭菜单
const handleClickOutside = (event) => {
  if (userMenuRef.value && !userMenuRef.value.contains(event.target)) {
    showUserMenu.value = false
  }
  if (kbDropdownRef.value && !kbDropdownRef.value.contains(event.target)) {
    showKbDropdown.value = false
  }
  if (webSearchDropdownRef.value && !webSearchDropdownRef.value.contains(event.target)) {
    showWebSearchSettings.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  adjustTextareaHeight()
  fetchConversations()
  fetchKnowledgeBases()
  loadLLMConfig()
  loadWebSearchConfig()
  
  // 注册全局函数，用于 markdown 中的引用标记点击
  window.showKbSourceDialog = (index, encodedContent) => {
    try {
      const content = decodeURIComponent(atob(encodedContent).split('').map(c => 
        '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)
      ).join(''))
      showSourceDialog(null, 'chunk', { index, content })
    } catch (e) {
      console.error('Failed to decode source content:', e)
    }
  }
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
  // 清理全局函数
  delete window.showKbSourceDialog
})
</script>

<style scoped>
/* 列表过渡动画 */
.list-enter-active,
.list-leave-active {
  transition: all 0.4s ease;
}
.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

/* 隐藏滚动条 */
.scrollbar-hide::-webkit-scrollbar {
    display: none;
}
.scrollbar-hide {
    -ms-overflow-style: none;
    scrollbar-width: none;
}

/* 展开动画 */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s ease;
  overflow: hidden;
}
.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
}
.expand-enter-to,
.expand-leave-from {
  opacity: 1;
  max-height: 500px;
}

/* 行数限制 */
.line-clamp-4 {
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 思考过程样式 */
.thinking-box {
  background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%);
  border-color: #e9d5ff;
}

.thinking-step {
  animation: fadeInUp 0.3s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.step-number {
  margin-top: 2px;
}

.step-content {
  line-height: 1.5;
}
</style>
