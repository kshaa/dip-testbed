package diptestbed.domain

import org.scalatest.freespec.AnyFreeSpec
import org.scalatest.matchers.should.Matchers

class HardwareCameraStateSpec extends AnyFreeSpec with Matchers {
  "hardware camera state should store initial chunks in order" in {
    val state = HardwareCameraState.initial[String](
      "self", "camera", "pubSubMediator", List.empty, HardwareListenerHeartbeatConfig.default())
    val first = Array(65.toByte, 66.toByte)
    val second = Array(67.toByte, 68.toByte)
    val third = Array(69.toByte, 70.toByte)
    val stateWithChunks = state.copy(initialChunks = third :: second :: first :: state.initialChunks)
    val chunks = stateWithChunks.initialChunkArray().toList.map(_.toInt)
    val expectation = List(65, 66, 67, 68, 69, 70)

    assert(chunks.length == expectation.length)
    chunks.zipAll(expectation, 0, 0).foreach { case (a, b) =>
      assert(a == b)
    }
  }
}
