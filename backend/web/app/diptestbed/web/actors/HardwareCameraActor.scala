package diptestbed.web.actors

import akka.actor._
import akka.util.ByteString
import cats.effect.IO
import cats.effect.unsafe.IORuntime
import cats.implicits.toBifunctorOps
import io.circe.parser.decode
import com.typesafe.scalalogging.LazyLogging
import diptestbed.domain.EventEngine.MessageResult
import diptestbed.domain.HardwareCameraMessage.{CameraChunk, EndLifecycle, StartLifecycle}
import diptestbed.domain._
import diptestbed.web.actors.ActorHelper.websocketFlowTransformer
import play.api.http.websocket.{BinaryMessage, CloseCodes, CloseMessage, TextMessage}
import play.api.mvc.WebSocket.MessageFlowTransformer
import io.circe.syntax._
import diptestbed.protocol.Codecs._

class HardwareCameraActor(
  val pubSubMediator: ActorRef,
  val camera: ActorRef,
  val hardwareIds: List[HardwareId],
)(implicit
  val iort: IORuntime,
) extends PubSubEngineActor[HardwareCameraState[ActorRef], HardwareCameraMessage, HardwareCameraEvent[ActorRef]]
    with Actor
    with LazyLogging {
  val startMessage: Option[HardwareCameraMessage] = Some(StartLifecycle())
  val endMessage: Option[HardwareCameraMessage] = Some(EndLifecycle())
  var state: HardwareCameraState[ActorRef] =
    HardwareCameraState.initial(self, camera, pubSubMediator, hardwareIds, HardwareListenerHeartbeatConfig.default())

  override def receiveMessage: PartialFunction[Any, (Some[ActorRef], HardwareCameraMessage)] = {
    case message: HardwareCameraMessage => (Some(sender()), message)
  }

  def onMessage(
    inquirer: => Option[ActorRef],
  ): HardwareCameraMessage => MessageResult[IO, HardwareCameraEvent[ActorRef], HardwareCameraState[ActorRef]] =
    HardwareCameraEventEngine.onMessage[ActorRef, IO](
      state,
      IO(state.self ! PoisonPill),
      send,
      publish,
      subscriptionMessage,
      inquirer)
}

object HardwareCameraActor {
  def props(
    pubSubMediator: ActorRef,
    out: ActorRef,
    hardwareIds: List[HardwareId],
  )(implicit
    iort: IORuntime,
  ): Props = Props(new HardwareCameraActor(pubSubMediator, out, hardwareIds))

  val cameraControlTransformer: MessageFlowTransformer[HardwareCameraMessage, HardwareCameraMessage] =
    websocketFlowTransformer({
      case TextMessage(text) => decode[HardwareCameraMessageExternal](text)
          .leftMap(e => CloseMessage(Some(CloseCodes.Unacceptable), e.getMessage))
      case BinaryMessage(bytes: ByteString) =>
        Right(CameraChunk(bytes.toArray))
    }, {
      case m: HardwareCameraMessageExternal => TextMessage(m.asJson.toString())
      case _ => CloseMessage(Some(CloseCodes.Unacceptable), "Server actor outputting unknown message")
    })
}


