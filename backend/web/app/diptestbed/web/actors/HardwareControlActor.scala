package diptestbed.web.actors

import akka.actor._
import akka.cluster.pubsub.DistributedPubSubMediator.Publish
import diptestbed.domain._
import play.api.http.websocket._
import play.api.mvc.WebSocket.MessageFlowTransformer
import io.circe.parser.decode
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
import diptestbed.protocol.Codecs._
import diptestbed.web.actors.ActorHelper._
import diptestbed.web.actors.QueryActor.Promise
import io.circe.syntax.EncoderOps

class HardwareControlActor(
  pubSubMediator: ActorRef,
  agent: ActorRef,
  hardwareId: HardwareId,
)(implicit
  iort: IORuntime,
) extends Actor
    with LazyLogging {
  var state: HardwareControlState[ActorRef] =
    HardwareControlState.initial(self, agent, hardwareId, HardwareListenerHeartbeatConfig.default())

  def setState(newState: HardwareControlState[ActorRef]): Unit = {
    state = newState
  }

  def send(actorRef: ActorRef, message: Any): IO[Unit] =
    IO(actorRef ! message)

  def publish(topic: PubSubTopic, message: HardwareControlMessage): IO[Unit] =
    send(pubSubMediator, Publish(topic.text(), message))

  def onMessage(
    inquirer: => Option[ActorRef],
  ): HardwareControlMessage => MessageResult[IO, HardwareControlEvent[ActorRef], HardwareControlState[ActorRef]] =
    HardwareControlEventEngine.onMessage[ActorRef, IO](state, send, publish, inquirer)

  def unsafeMaterializeResult(
    result: MessageResult[IO, HardwareControlEvent[ActorRef], HardwareControlState[ActorRef]],
  ): Unit = EventEngine.unsafeMaterializeMessageResultIO(result, setState)

  override def preStart(): Unit = {
    super.preStart()
    unsafeMaterializeResult(onMessage(None)(StartLifecycle()))
  }

  override def receive: Receive = {
    case message: HardwareControlMessage =>
      unsafeMaterializeResult(onMessage(Some(sender()))(message))

    // This is an old, dumb workaround, should be removed and tested
    case Promise(inquirer, message: HardwareControlMessage) =>
      unsafeMaterializeResult(onMessage(Some(inquirer))(message))

    case Terminated => unsafeMaterializeResult(onMessage(None)(EndLifecycle()))
  }

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
