package diptestbed.web.actors

import akka.actor._
import diptestbed.domain._
import io.circe.syntax.EncoderOps
import akka.cluster.pubsub.DistributedPubSubMediator.Subscribe
import cats.effect.IO
import diptestbed.web.actors.HardwareControlActor._
import cats.effect.unsafe.IORuntime
import akka.util.{ByteString, Timeout}
import cats.data.EitherT
import cats.implicits.toBifunctorOps
import io.circe.parser.decode

import scala.annotation.unused
import com.typesafe.scalalogging.LazyLogging
import diptestbed.database.services.{HardwareService, UserService}
import diptestbed.domain.HardwareControlMessageExternalBinary._
import diptestbed.domain.HardwareControlMessageExternalNonBinary._
import diptestbed.domain.HardwareSerialMonitorMessageBinary._
import diptestbed.domain.HardwareSerialMonitorMessageNonBinary._
import diptestbed.domain.HardwareControlMessageInternal.SerialMonitorListenersHeartbeatPing
import diptestbed.web.actors.ActorHelper.websocketFlowTransformer
import play.api.http.websocket._
import play.api.mvc.WebSocket.MessageFlowTransformer
import scala.concurrent.duration.DurationInt
import diptestbed.protocol.HardwareControlCodecs._
import diptestbed.protocol.HardwareSerialMonitorCodecs._

class HardwareSerialMonitorListenerActor(
  pubSubMediator: ActorRef,
  userService: UserService[IO],
  hardwareService: HardwareService[IO],
  out: ActorRef,
  hardwareId: HardwareId,
  serialConfig: Option[SerialConfig],
)(implicit
  actorSystem: ActorSystem,
  iort: IORuntime,
  @unused timeout: Timeout,
) extends Actor
    with LazyLogging {
  logger.info(s"Serial monitor listener for hardware #${hardwareId} spawned")

  var auth: Option[User] = None

  // Send monitor actor request for listening w/ a given baudrate and react accordingly
  def requestMonitorInit(): IO[Unit] = requestSerialMonitor(hardwareId, serialConfig).value
    .flatMap {
      case Right(_) =>
        // Start listening to serial monitor topic
        IO(pubSubMediator ! Subscribe(hardwareId.serialBroadcastTopic().text(), self))
      case Left(error) =>
        // Send error to listener
        val message: HardwareSerialMonitorMessageNonBinary = MonitorUnavailable(error)
        sendToListener(message) >>
          // Stop this listener
          killListener("Monitor unavailable")
    }
    .void

  def sendToListener(message: HardwareSerialMonitorMessage): IO[Unit] =
    IO(out ! message)

  def killListener(reason: String): IO[Unit] = {
    // Stop websocket listener
    IO.sleep(5.seconds) >>
      IO(out ! ConnectionClosed(reason)) >>
      // Stop this actor
      IO(self ! PoisonPill)
  }

  def checkAuth(username: String, password: String): IO[Either[String, User]] =
    (for {
      user <- EitherT(userService.getUserWithPassword(username, password))
        .leftMap(e => f"Database error: ${e.message}")
      existingUser <- EitherT.fromEither[IO](user.toRight(f"User auth failure"))
      _ <- EitherT.fromEither[IO](Either.cond(
        existingUser.canInteractHardware, (), "Missing permission: Hardware access"))
      hardware <- EitherT(hardwareService.getHardware(Some(existingUser), hardwareId, write = false))
        .leftMap(e => f"Database error: ${e.message}")
      _ <- EitherT.fromEither[IO](hardware.toRight(f"Hardware does not exist or you're missing permissions"))
    } yield existingUser).value

  def receive: Receive = {
    // Initial hardware monitoring request to hardware control failed
    case badMessage: HardwareSerialMonitorMessageNonBinary.MonitorUnavailable =>
      val message: HardwareSerialMonitorMessage = badMessage
      (sendToListener(message) >> killListener("Monitor not valid anymore")).unsafeRunAsync(_ => ())
    // Hardware monitoring failed later in lifecycle
    case badMessage: HardwareControlMessageExternalNonBinary.SerialMonitorUnavailable =>
      val message: HardwareSerialMonitorMessage =
        HardwareSerialMonitorMessageNonBinary.MonitorUnavailable(badMessage.reason)
      (sendToListener(message) >> killListener("Monitor not valid anymore")).unsafeRunAsync(_ => ())
    // Hardware control published message to listeners
    case serialToClientMessage: SerialMonitorMessageToClient =>
      if (auth.isDefined) {
        val message: HardwareSerialMonitorMessage = SerialMessageToClient(serialToClientMessage.message.bytes)
        sendToListener(message).unsafeRunAsync(_ => ())
      }
    // Hardware control published heartbeat request to listeners
    case _: SerialMonitorListenersHeartbeatPing =>
      sendToHardwareActor(hardwareId, SerialMonitorListenersHeartbeatPong()).value.unsafeRunAsync(_ => ())
    // Listener is sending a message to hardware control
    case serialToAgentMessage: SerialMonitorMessageToAgent =>
      if (auth.isDefined) {
        sendToHardwareActor(hardwareId, serialToAgentMessage).value.unsafeRunAsync(_ => ())
      }
    // Listener sent auth request, validate, write in state and respond with result
    case m: HardwareControlMessageExternalNonBinary.AuthRequest =>
      checkAuth(m.username, m.password).flatMap[Unit] {
        case Left(reason) =>
          IO {
            auth = None
          } >>
            sendToListener(AuthResult(Some(reason))) >>
            killListener("Auth failed")
        case Right(user) =>
          IO {
            auth = Some(user)
          } >>
            requestMonitorInit() >>
            sendToListener(AuthResult(None))
      }.unsafeRunAsync(_ => ())
  }
}

object HardwareSerialMonitorListenerActor {
  def props(
    pubSubMediator: ActorRef,
    userService: UserService[IO],
    hardwareService: HardwareService[IO],
    out: ActorRef,
    hardwareId: HardwareId,
    serialConfig: Option[SerialConfig],
  )(implicit
    iort: IORuntime,
    timeout: Timeout,
    actorSystem: ActorSystem,
  ): Props = Props(new HardwareSerialMonitorListenerActor(
    pubSubMediator, userService, hardwareService, out, hardwareId, serialConfig))

  val listenerTransformer: MessageFlowTransformer[HardwareControlMessage, HardwareSerialMonitorMessage] =
    websocketFlowTransformer(
      {
        case TextMessage(text) =>
          decode[HardwareControlMessageNonBinary](text)
            .flatMap {
              case HardwareControlMessageInternal.AuthResult(_) => Left(new Exception("Can't force auth externally"))
              case HardwareControlMessageInternal.AuthSuccess(_) => Left(new Exception("Can't force auth externally"))
              case HardwareControlMessageInternal.AuthFailure(_) => Left(new Exception("Can't force auth externally"))
              case other => Right(other)
            }
            .leftMap(e => CloseMessage(Some(CloseCodes.Unacceptable), e.getMessage))
        case BinaryMessage(bytes: ByteString) =>
          Right(SerialMonitorMessageToAgent(SerialMessageToAgent(bytes.toArray)))
      },
      {
        case m: SerialMessageToAgent                  => BinaryMessage(ByteString.fromArray(m.bytes))
        case m: SerialMessageToClient                 => BinaryMessage(ByteString.fromArray(m.bytes))
        case ConnectionClosed(reason)                 => CloseMessage(0, reason)
        case m: HardwareSerialMonitorMessageNonBinary => TextMessage(m.asJson.noSpaces)
      },
    )

}
