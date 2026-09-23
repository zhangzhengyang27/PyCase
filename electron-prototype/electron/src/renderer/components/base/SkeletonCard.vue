<template>
  <!-- SkeletonCard：画廊首载骨架卡（与 ExampleCard 同构的占位块） -->
  <div class="surface-card p-3.5 flex flex-col gap-3 animate-pulse [content-visibility:auto] [contain-intrinsic-size:auto_170px]">
    <div class="flex items-center gap-2.5">
      <div class="w-9 h-9 rounded-control bg-hover shrink-0"></div>
      <div class="flex-1 min-w-0 space-y-1.5">
        <div class="h-3 w-3/5 rounded bg-card"></div>
        <div class="h-2.5 w-2/5 rounded bg-card"></div>
      </div>
    </div>
    <div class="space-y-1.5">
      <div class="h-2.5 w-full rounded bg-card"></div>
      <div class="h-2.5 w-4/5 rounded bg-card"></div>
      <div class="h-2.5 w-3/5 rounded bg-card"></div>
    </div>
  </div>
</template>
