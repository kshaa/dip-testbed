package diptestbed.domain

import cats.data.NonEmptyList
import cats.effect.Temporal
import cats.implicits.catsSyntaxFlatMapOps
import diptestbed.domain.EventEngine.MessageResult
import diptestbed.domain.HardwareCameraListenerEvent._
import diptestbed.domain.HardwareCameraListenerMessage._
import diptestbed.domain.HardwareCameraMessage.{CameraListenersHeartbeatPong, CameraSubscription}
import scala.concurrent.duration.{DurationInt, FiniteDuration}

case class HardwareCameraListenerState[F[_], T](
  auth: Option[User],
  self: T,
  pubSubMediator: T,
  hardwareId: HardwareId,
  enqueue: Array[Byte] => F[Unit],
  fail: Exception => F[Unit],
  complete: F[Unit],
  maxLifetime: Option[FiniteDuration],
  initCheckTimeout: FiniteDuration,
  initialized: Boolean = false,
  ending: Boolean = false,
)

sealed trait HardwareCameraListenerMessage
object HardwareCameraListenerMessage {
  case class StartLifecycle() extends HardwareCameraListenerMessage
  case class EndLifecycle() extends HardwareCameraListenerMessage
  case class CheckInitialization() extends HardwareCameraListenerMessage
  case class ListenerCameraDropped(reason: String) extends HardwareCameraListenerMessage
  case class ListenerCameraChunk(bytes: Array[Byte]) extends HardwareCameraListenerMessage
  case class ListenerCameraHeartbeat() extends HardwareCameraListenerMessage
}

sealed trait HardwareCameraListenerEvent
object HardwareCameraListenerEvent {
  case class StartedLifecycle() extends HardwareCameraListenerEvent
  case class EndedLifecycle() extends HardwareCameraListenerEvent
  case class CheckingInitialization() extends HardwareCameraListenerEvent
  case class CameraDropped(reason: String) extends HardwareCameraListenerEvent
  case class ReceivedCameraChunk(bytes: Array[Byte]) extends HardwareCameraListenerEvent
  case class ReceivedCameraHeartbeat() extends HardwareCameraListenerEvent
}

object HardwareCameraListenerLogic {
  def onMessage[A, F[_]: Temporal](
    lastState: => HardwareCameraListenerState[F, A],
    send: (A, Any) => F[Unit],
    publish: (PubSubTopic, Any) => F[Unit],
    subscriptionMessage: (PubSubTopic, A) => Any
  ): HardwareCameraListenerMessage => MessageResult[F, HardwareCameraListenerEvent, HardwareCameraListenerState[F, A]] = {
    case StartLifecycle() => Right(NonEmptyList.of((
      StartedLifecycle(),
      lastState,
      Some((List(
        // Announce subscriber to camera
        publish(lastState.hardwareId.cameraMetaTopic(), CameraSubscription()),
        // Subscribe to video stream
        send(lastState.pubSubMediator, subscriptionMessage(lastState.hardwareId.cameraBroacastTopic(), lastState.self)),
        // Check if any chunk received
        implicitly[Temporal[F]].sleep(lastState.initCheckTimeout) >>
          send(lastState.self, CheckInitialization())
      ) ++
        // Force stream lifetime
        lastState.maxLifetime.map(time =>
          implicitly[Temporal[F]].sleep(time) >>
            send(lastState.self, ListenerCameraDropped("Listener end of lifetime reached"))))
        .reduce(_ >> _))
    )))
    case EndLifecycle() => Right(NonEmptyList.of((
      EndedLifecycle(),
      lastState,
      Some(lastState.fail(new Exception("Unexpected end of camera stream")))
    )))
    case CheckInitialization() => Right(NonEmptyList.of((
      CheckingInitialization(),
      lastState,
      Option.when(!lastState.initialized)(lastState.fail(new Exception("Failed to initialize stream")))
    )))
    case ListenerCameraDropped(reason) => Right(NonEmptyList.of((
      CameraDropped(reason),
      lastState.copy(ending = true),
      Some(lastState.fail(new Exception(s"Camera stream dropped, reason: ${reason}")))
    )))
    case ListenerCameraChunk(bytes) => Right(NonEmptyList.of((
      ReceivedCameraChunk(bytes),
      lastState.copy(initialized = true),
      {
//        // Initially subscribe to camera video stream chunks
//        val init = Option.when(!lastState.initialized)(
//          send(lastState.pubSubMediator, subscriptionMessage(lastState.hardwareId.cameraBroacastTopic(), lastState.self))
//        ).toList
//        // Forward chunk to listener queue
//        val forward = Option.when(!lastState.ending && bytes.length > 0)(lastState.enqueue(bytes)).toList
//        val tasks = init ++ forward
//        tasks.foldLeft[Option[F[Unit]]](None) {
//          case (None, b) => Some(b)
//          case (Some(a), b) => Some(a >> b)
//        }

        // Forward chunk to listener queue
        Option.when(!lastState.ending && bytes.length > 0)(lastState.enqueue(bytes))
      }
    )))
    case ListenerCameraHeartbeat() => Right(NonEmptyList.of((
      ReceivedCameraHeartbeat(),
      lastState,
      Some(publish(lastState.hardwareId.cameraMetaTopic(), CameraListenersHeartbeatPong()))
    )))
  }
}