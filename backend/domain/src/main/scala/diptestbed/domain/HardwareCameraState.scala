package diptestbed.domain

case class HardwareCameraState[A](
  self: A,
  camera: A,
  pubSubMediator: A,
  hardwareIds: List[HardwareId],
  listenerHeartbeatsReceived: Int,
  listenerHeartbeatConfig: HardwareListenerHeartbeatConfig,
  initialChunks: List[Array[Byte]],
  broadcasting: Boolean,
  maxInitialChunks: Int) {
  def initialChunkArray(): Array[Byte] =
    initialChunks.reverse.foldLeft(Array.empty[Byte]){ case (array, chunk) =>
      array ++ chunk
    }
}

object HardwareCameraState {
  def initial[A](
    self: A,
    camera: A,
    pubSubMediator: A,
    hardwareIds: List[HardwareId],
    listenerHeartbeatConfig: HardwareListenerHeartbeatConfig,
  ): HardwareCameraState[A] =
    HardwareCameraState(
      self,
      camera,
      pubSubMediator,
      hardwareIds,
      0,
      listenerHeartbeatConfig,
      List.empty,
      broadcasting = false,
      10
    )
}
