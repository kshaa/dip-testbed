package diptestbed.web.actors

import akka.actor._
import diptestbed.domain._
import play.api.http.websocket._
import play.api.mvc.WebSocket.MessageFlowTransformer
import cats.effect.IO
import cats.effect.unsafe.IORuntime
import akka.util.{ByteString, Timeout}
import cats.data.EitherT
import cats.implicits.toBifunctorOps
import com.typesafe.scalalogging.LazyLogging
import diptestbed.database.services.{HardwareService, UserService}
import diptestbed.domain.EventEngine.MessageResult
import diptestbed.domain.HardwareControlMessageExternalBinary._
import diptestbed.domain.HardwareControlMessageExternalNonBinary._
import diptestbed.domain.HardwareControlMessageInternal._
import diptestbed.domain.HardwareSerialMonitorMessageBinary._
import io.circe.parser.decode
import io.circe.syntax.EncoderOps
import diptestbed.web.actors.ActorHelper._
import diptestbed.web.actors.QueryActor.Promise
import diptestbed.protocol.HardwareControlCodecs._

class HardwareControlActor(
  val appConfig: DIPTestbedConfig,
  val userService: UserService[IO],
  val hardwareService: HardwareService[IO],
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
    HardwareControlState.initial(
      self,
      agent,
      hardwareId,
      HardwareListenerHeartbeatConfig.fromConfig(appConfig))

  override def receiveMessage: PartialFunction[Any, (Some[ActorRef], HardwareControlMessage)] = {
    case message: HardwareControlMessage =>
      (Some(sender()), message)
    // This is an old, dumb workaround, should be removed and tested
    case Promise(inquirer, message: HardwareControlMessage) =>
      (Some(inquirer), message)
  }

  def auth(username: String, password: String): IO[Either[String, User]] =
    (for {
      user <- EitherT(userService.getUserWithPassword(username, password))
        .leftMap(e => f"Database error: ${e.message}")
      existingUser <- EitherT.fromEither[IO](user.toRight(f"User auth failure"))
      _ <- EitherT.fromEither[IO](Either.cond(
        existingUser.canInteractHardware, (), "Missing permission: Hardware access"))
      hardware <- EitherT(hardwareService.getHardware(Some(existingUser), hardwareId, write = true)) // Controlling hardware requires write permission
        .leftMap(e => f"Database error: ${e.message}")
      _ <- EitherT.fromEither[IO](hardware.toRight(f"Hardware does not exist or you're missing permissions"))
    } yield existingUser).value

  def onMessage(
    inquirer: => Option[ActorRef],
  ): HardwareControlMessage => MessageResult[IO, HardwareControlEvent[ActorRef], HardwareControlState[ActorRef]] =
    HardwareControlEventEngine.onMessage[ActorRef, IO](state, auth, send, publish, inquirer)
}

object HardwareControlActor {
  def props(
    appConfig: DIPTestbedConfig,
    userService: UserService[IO],
    hardwareService: HardwareService[IO],
    pubSubMediator: ActorRef,
    out: ActorRef,
    hardwareId: HardwareId,
  )(implicit
    iort: IORuntime,
  ): Props = Props(new HardwareControlActor(appConfig, userService, hardwareService, pubSubMediator, out, hardwareId))

  val controlTransformer: MessageFlowTransformer[HardwareControlMessage, HardwareControlMessage] =
    websocketFlowTransformer(
      {
        case TextMessage(text) =>
          decode[HardwareControlMessageNonBinary](text)
            .flatMap {
                case AuthResult(_) => Left(new Exception("Can't force auth externally"))
                case AuthSuccess(_) => Left(new Exception("Can't force auth externally"))
                case AuthFailure(_) => Left(new Exception("Can't force auth externally"))
                case other => Right(other)
            }
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
