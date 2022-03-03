package diptestbed.web.actors

import akka.actor._
import diptestbed.domain._
import play.api.http.websocket._
import play.api.mvc.WebSocket.MessageFlowTransformer
import cats.effect.IO
import cats.implicits._
import cats.effect.unsafe.IORuntime
import akka.util.{ByteString, Timeout}
import cats.data.EitherT
import com.typesafe.scalalogging.LazyLogging
import diptestbed.domain.EventEngine.MessageResult
import diptestbed.domain.HardwareControlMessageExternalBinary._
import diptestbed.domain.HardwareControlMessageExternalNonBinary._
import diptestbed.domain.HardwareControlMessageInternal._
import diptestbed.domain.HardwareSerialMonitorMessageBinary._
import io.circe.parser.decode
import diptestbed.protocol.Codecs._
import io.circe.syntax.EncoderOps
import diptestbed.web.actors.ActorHelper._
import diptestbed.web.actors.QueryActor.Promise

class HardwareControlActor(
  val pubSubMediator: ActorRef,
  val agent: ActorRef,
  val hardwareId: HardwareId,
)(implicit
  val iort: IORuntime,
) extends PubSubEngineActor[HardwareControlState[ActorRef], HardwareControlMessage, HardwareControlEvent[ActorRef]]
    with Actor
    with LazyLogging {
  val startMessage: Option[HardwareControlMessage] = Some(StartLifecycle())
  val endMessage: Option[HardwareControlMessage] = Some(EndLifecycle())
  var state: HardwareControlState[ActorRef] =
    HardwareControlState.initial(self, agent, hardwareId, HardwareListenerHeartbeatConfig.default())

  override def receiveMessage: PartialFunction[Any, (Some[ActorRef], HardwareControlMessage)] = {
    case message: HardwareControlMessage =>
      (Some(sender()), message)
    // This is an old, dumb workaround, should be removed and tested
    case Promise(inquirer, message: HardwareControlMessage) =>
      (Some(inquirer), message)
  }

  def onMessage(
    inquirer: => Option[ActorRef],
  ): HardwareControlMessage => MessageResult[IO, HardwareControlEvent[ActorRef], HardwareControlState[ActorRef]] =
    HardwareControlEventEngine.onMessage[ActorRef, IO](state, send, publish, inquirer)
}

object HardwareControlActor {
  def props(
    pubSubMediator: ActorRef,
    out: ActorRef,
    hardwareId: HardwareId,
  )(implicit
    iort: IORuntime,
  ): Props = Props(new HardwareControlActor(pubSubMediator, out, hardwareId))

  val controlTransformer: MessageFlowTransformer[HardwareControlMessage, HardwareControlMessage] =
    websocketFlowTransformer(
      {
        case TextMessage(text) =>
          decode[HardwareControlMessageNonBinary](text)
            .leftMap(e => CloseMessage(Some(CloseCodes.Unacceptable), e.getMessage))
        case BinaryMessage(bytes: ByteString) =>
          Right(SerialMonitorMessageToClient(SerialMessageToClient(bytes.toArray)))
      },
      {
        case m: HardwareControlMessageNonBinary => TextMessage(m.asJson.noSpaces)
        case m: SerialMonitorMessageToAgent     => BinaryMessage(ByteString.fromArray(m.message.bytes))
        case m: SerialMonitorMessageToClient    => BinaryMessage(ByteString.fromArray(m.message.bytes))
      },
    )

  def requestSerialMonitor(
    hardwareId: HardwareId,
    serialConfig: Option[SerialConfig],
  )(implicit actorSystem: ActorSystem, t: Timeout, iort: IORuntime): EitherT[IO, String, Unit] =
    for {
      hardwareRef <- resolveActorRef(UserPrefixedActorPath(hardwareId.actorId()).text())(actorSystem, implicitly)
      result <- QueryActor.queryActorT(
        hardwareRef,
        actorRef => Promise(actorRef, SerialMonitorRequest(serialConfig)),
        immediate = false,
      )
      monitorResult <- EitherT.fromEither[IO](result match {
        case SerialMonitorResult(result) => result.toLeft(())
        case _                           => Left("Hardware responded with an invalid response")
      })
    } yield monitorResult

  def sendToHardwareActor(
    hardwareId: HardwareId,
    serialMessage: HardwareControlMessage,
  )(implicit actorSystem: ActorSystem, t: Timeout): EitherT[IO, String, Unit] =
    for {
      hardwareRef <- resolveActorRef(UserPrefixedActorPath(hardwareId.actorId()).text())(actorSystem, implicitly)
      _ <- EitherT.liftF(IO(hardwareRef ! serialMessage))
    } yield ()

  def requestSoftwareUpload(
    hardwareId: HardwareId,
    softwareId: SoftwareId,
  )(implicit actorSystem: ActorSystem, t: Timeout, iort: IORuntime): EitherT[IO, String, Unit] =
    for {
      hardwareRef <- resolveActorRef(UserPrefixedActorPath(hardwareId.actorId()).text())
      result <- QueryActor.queryActorT(
        hardwareRef,
        actorRef => Promise(actorRef, UploadSoftwareRequest(softwareId)),
        immediate = false,
      )
      uploadResult <- EitherT.fromEither[IO](result match {
        case UploadSoftwareResult(result) => result.toLeft(())
        case _                            => Left("Hardware responded with an invalid response")
      })
    } yield uploadResult
}
