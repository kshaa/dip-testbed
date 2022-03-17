package diptestbed.web.actors

import akka.actor._
import akka.util.ByteString
import cats.data.EitherT
import cats.effect.IO
import cats.effect.unsafe.IORuntime
import io.circe.parser.decode
import com.typesafe.scalalogging.LazyLogging
import diptestbed.database.services.{HardwareService, UserService}
import diptestbed.domain.EventEngine.MessageResult
import diptestbed.domain.HardwareCameraMessage._
import diptestbed.domain._
import diptestbed.web.actors.ActorHelper.websocketFlowTransformer
import play.api.http.websocket.{BinaryMessage, CloseCodes, CloseMessage, TextMessage}
import play.api.mvc.WebSocket.MessageFlowTransformer
import io.circe.syntax._
import cats.implicits._
import diptestbed.protocol.HardwareCameraCodecs._

class HardwareCameraActor(
  val appConfig: DIPTestbedConfig,
  val userService: UserService[IO],
  val hardwareService: HardwareService[IO],
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
    HardwareCameraState.initial(
      self,
      camera,
      pubSubMediator,
      hardwareIds,
      HardwareListenerHeartbeatConfig.fromConfig(appConfig))

  override def receiveMessage: PartialFunction[Any, (Some[ActorRef], HardwareCameraMessage)] = {
    case message: HardwareCameraMessage => (Some(sender()), message)
  }

  def auth(username: String, password: String): IO[Either[String, User]] =
    (for {
      user <- EitherT(userService.getUserWithPassword(username, password))
        .leftMap(e => f"Database error: ${e.message}")
      existingUser <- EitherT.fromEither[IO](user.toRight(f"User auth failure"))
      _ <- EitherT.fromEither[IO](Either.cond(
        existingUser.canInteractHardware, (), "Missing permission: Hardware access"))
      // Inefficient - queries should be batched into one
      hardware <- hardwareIds.traverse(id => EitherT(hardwareService.getHardware(Some(existingUser), id, write = true))) // Controlling hardware requires write permission
        .leftMap(e => f"Database error: ${e.message}")
      _ <- EitherT.fromEither[IO](Either.cond(hardware.exists(_.isDefined), (), f"Hardware does not exist or you're missing permissions"))
    } yield existingUser).value

  def onMessage(
    inquirer: => Option[ActorRef],
  ): HardwareCameraMessage => MessageResult[IO, HardwareCameraEvent[ActorRef], HardwareCameraState[ActorRef]] =
    HardwareCameraEventEngine.onMessage[ActorRef, IO](
      state,
      IO(state.self ! PoisonPill),
      auth,
      send,
      publish,
      subscriptionMessage,
      inquirer)
}

object HardwareCameraActor {
  def props(
    appConfig: DIPTestbedConfig,
    userService: UserService[IO],
    hardwareService: HardwareService[IO],
    pubSubMediator: ActorRef,
    out: ActorRef,
    hardwareIds: List[HardwareId],
  )(implicit
    iort: IORuntime,
  ): Props = Props(new HardwareCameraActor(appConfig, userService, hardwareService, pubSubMediator, out, hardwareIds))

  val cameraControlTransformer: MessageFlowTransformer[HardwareCameraMessage, HardwareCameraMessage] =
    websocketFlowTransformer({
      case TextMessage(text) => decode[HardwareCameraMessageExternal](text)
        .flatMap {
          case AuthResult(_) => Left(new Exception("Can't force auth externally"))
          case other => Right(other)
        }
        .leftMap(e => CloseMessage(Some(CloseCodes.Unacceptable), e.getMessage))
      case BinaryMessage(bytes: ByteString) =>
        Right(CameraChunk(bytes.toArray))
    }, {
      case m: HardwareCameraMessageExternal => TextMessage(m.asJson.toString())
      case _ => CloseMessage(Some(CloseCodes.Unacceptable), "Server actor outputting unknown message")
    })
}


