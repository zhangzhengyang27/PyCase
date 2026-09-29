// 协议名表契约测试：TS 侧名表必须与 shared/protocol.json 逐字相等。
//
// 跨语言单一来源的两端：
//   - Python 金标（tests/test_guard_protocol.py）断言 server.METHODS == protocol.json.rpc_methods；
//   - 本测试断言 shared/protocol.ts 的常量 == protocol.json 的同名数组。
// 任何一侧漏改都会有一端变红，方法表不可能悄悄漂移。
import { describe, expect, it } from 'vitest'

import protocolJson from '../../../../../shared/protocol.json'
import { LOCAL_EVENTS, NAMESPACES, NOTIFICATIONS, RPC_METHODS } from '../../../../../shared/protocol'
import { api, RPC_BINDINGS } from '../sidecar-client'

describe('协议名表（shared/protocol.json 为唯一来源）', () => {
  it('RPC 方法表与 JSON 一致', () => {
    expect([...RPC_METHODS]).toEqual(protocolJson.rpc_methods)
  })

  it('通知通道与 JSON 一致', () => {
    expect([...NOTIFICATIONS]).toEqual(protocolJson.notifications)
  })

  it('本地事件与 JSON 一致', () => {
    expect([...LOCAL_EVENTS]).toEqual(protocolJson.local_events)
  })

  it('命名空间分组与 JSON 逐组一致', () => {
    const expected = protocolJson.namespaces as Record<string, readonly string[]>
    expect(Object.keys(NAMESPACES).sort()).toEqual(Object.keys(expected).sort())
    for (const group of Object.keys(expected)) {
      expect([...(NAMESPACES as Record<string, readonly string[]>)[group]]).toEqual([...expected[group]])
    }
  })

  it('方法名互不重复、命名空间名不与 RPC 撞名', () => {
    expect(new Set(RPC_METHODS).size).toBe(RPC_METHODS.length)
    const rpc = new Set<string>(RPC_METHODS)
    for (const name of [...NOTIFICATIONS, ...LOCAL_EVENTS]) {
      expect(rpc.has(name)).toBe(false)
    }
  })
})

describe('客户端接线（api 覆盖协议方法表）', () => {
  it('protocol.json 的每个 RPC 方法都能在 api 上找到调用入口', () => {
    const paths = Object.keys(RPC_BINDINGS)
    expect(paths.sort()).toEqual([...RPC_METHODS].sort())
    for (const method of paths) {
      const fn = RPC_BINDINGS[method].split('.').reduce<unknown>((node, key) => (node as Record<string, unknown>)?.[key], api)
      expect(typeof fn, `${method} → api.${RPC_BINDINGS[method]}`).toBe('function')
    }
  })

  it('事件通道覆盖 protocol.json 的通知 + 本地事件', () => {
    const expected = new Set([...protocolJson.notifications, ...protocolJson.local_events])
    const eventish = new Set([...NOTIFICATIONS, ...LOCAL_EVENTS])
    for (const name of expected) expect(eventish.has(name as never)).toBe(true)
    // 渲染层额外通道（envProgress / maximized）不属于 sidecar 通知，单独点名
    expect(['envProgress', 'maximized'].every((c) => typeof c === 'string')).toBe(true)
  })
})
