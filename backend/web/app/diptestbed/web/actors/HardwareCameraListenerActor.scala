package diptestbed.web.actors

import akka.NotUsed
import akka.actor._
import akka.stream.{Materializer, OverflowStrategy}
import akka.stream.scaladsl.{Source, SourceQueueWithComplete}
import cats.data.EitherT
import cats.effect.IO
import cats.effect.unsafe.IORuntime
import com.typesafe.scalalogging.LazyLogging
import diptestbed.domain.EventEngine.MessageResult
import diptestbed.domain.HardwareCameraListenerMessage.{EndLifecycle, StartLifecycle}
import diptestbed.domain._
import scala.concurrent.duration.DurationInt
import scala.util.Try

class HardwareCameraListenerActor(
  val appConfig: DIPTestbedConfig,
  val pubSubMediator: ActorRef,
  val hardwareId: HardwareId,
  val queue: SourceQueueWithComplete[Array[Byte]]
)(implicit
  val iort: IORuntime,
) extends PubSubEngineActor[
  HardwareCameraListenerState[IO, ActorRef],
  HardwareCameraListenerMessage,
  HardwareCameraListenerEvent
]
    with Actor
    with LazyLogging {
  println("Camera listener started")
  val startMessage: Option[HardwareCameraListenerMessage] = Some(StartLifecycle())
  val endMessage: Option[HardwareCameraListenerMessage] = Some(EndLifecycle())
  var state: HardwareCameraListenerState[IO, ActorRef] =
    HardwareCameraListenerState(
      None,
      self,
      pubSubMediator,
      hardwareId,
      bytes => IO.fromFuture(IO(queue.offer(bytes))).void,
      exception => IO(queue.fail(exception)) >> IO(self ! PoisonPill),
      IO(queue.complete()),
      Some(appConfig.maxStreamTime),
      appConfig.cameraInitTimeout)

  override def receiveMessage: PartialFunction[Any, (Some[ActorRef], HardwareCameraListenerMessage)] = {
    case message: HardwareCameraListenerMessage =>
      (Some(sender()), message)
  }

  def onMessage(
    inquirer: => Option[ActorRef],
  ): HardwareCameraListenerMessage => MessageResult[IO, HardwareCameraListenerEvent, HardwareCameraListenerState[IO, ActorRef]] =
    HardwareCameraListenerLogic.onMessage(
      state,
      send,
      publish,
      subscriptionMessage
    )
}


object HardwareCameraListenerActor {
  def props(
    appConfig: DIPTestbedConfig,
    pubSubMediator: ActorRef,
    hardwareId: HardwareId,
    queue: SourceQueueWithComplete[Array[Byte]]
  )(implicit
    iort: IORuntime,
  ): Props = Props(new HardwareCameraListenerActor(appConfig, pubSubMediator, hardwareId, queue))

  def spawnCameraSource(
    appConfig: DIPTestbedConfig,
    pubSubMediator: ActorRef,
    hardwareId: HardwareId)(implicit
    mat: Materializer,
    iort: IORuntime,
    actorSystem: ActorSystem
  ): EitherT[IO, String, Source[Array[Byte], NotUsed]] = {
    for {
      // Build source with queue
      prematerialized <- EitherT[IO, String, (SourceQueueWithComplete[Array[Byte]], Source[Array[Byte], NotUsed])](IO {
        val bufferSize = 100
        val overflowStrategy = OverflowStrategy.dropHead
        Right(Source.queue[Array[Byte]](bufferSize, overflowStrategy).preMaterialize())
      })

      // Spawn camera listener actor which forwards to the queue
      (queue, source) = prematerialized
      _ <- EitherT(IO {
        Try(actorSystem.actorOf(HardwareCameraListenerActor.props(appConfig, pubSubMediator, hardwareId, queue))).toEither
      }).leftMap(error => s"Failed to connect to camera, reason: ${error}")

      _ = source.recover(e => {
        println(s"Received exception: ${e}")
        Array.empty
      })
    } yield source
  }

}