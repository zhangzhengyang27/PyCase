// 协议名表契约测试：TS 侧名表必须与 shared/protocol.json 逐字相等。
//
// 跨语言单一来源的两端：
//   - Python 金标（tests/test_guard_protocol.py）断言 server.METHODS == protocol.json.rpc_methods；
//   - 本测试断言 shared/protocol.ts 的常量 == protocol.json 的同名数组。
// 任何一侧漏改都会有一端变红，方法表不可能悄悄漂移。
import { describe, expect, it } from 'vitest'

import protocolJson from '../../../../../shared/protocol.json'
import { LOCAL_EVENTS, NAMESPACES, NOTIFICATIONS, RPC_METHODS } from '../../../../../shared/protocol'

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
