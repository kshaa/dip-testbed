package iotfrisbee.web.actors

import akka.actor.{Actor, ActorRef, Props}
import iotfrisbee.domain.{HardwareId, HardwareControlMessage => Control}
import play.api.http.websocket.{CloseCodes, CloseMessage, WebSocketCloseException}
import play.api.mvc.WebSocket.MessageFlowTransformer
import io.circe.parser.decode
import io.circe.syntax.EncoderOps
import iotfrisbee.protocol.Codecs.{hardwareControlMessageDecoder, hardwareControlMessageEncoder}
import akka.cluster.pubsub.DistributedPubSubMediator.Publish
import cats.effect.IO
import iotfrisbee.web.actors.HardwareControlActor.hardwareEventTopic
import cats.effect.unsafe.IORuntime
import iotfrisbee.domain.HardwareControlMessage.{UploadSoftwareRequest, UploadSoftwareResult}
import akka.util.Timeout
import cats.implicits.catsSyntaxOptionId
import scala.annotation.unused
import com.typesafe.scalalogging.LazyLogging
import iotfrisbee.web.actors.HardwareControlState.{Initial, Uploading}
import iotfrisbee.web.actors.QueryActor.Promise

sealed trait HardwareControlState {}
object HardwareControlState {
  case object Initial extends HardwareControlState
  case class Uploading(requester: Option[ActorRef]) extends HardwareControlState
}

class HardwareControlActor(
  pubSubMediator: ActorRef,
  out: ActorRef,
  hardwareId: HardwareId
)(implicit
  iort: IORuntime,
  @unused timeout: Timeout
) extends Actor with LazyLogging {
  logger.info(s"Actor for hardware #${hardwareId} spawned")

  val eventTopic: String = hardwareEventTopic(hardwareId)
  var state: HardwareControlState = Initial

  def receive: Receive = {
    case controlMessage: Control => {
      logger.info(s"Receiving anonymous control message: ${controlMessage}")
      receiveControl(None, controlMessage)
    }
    case Promise(inquirer, controlMessage: Control) => {
      logger.info(s"Inquirer '${inquirer}' sent control message: ${controlMessage}")
      receiveControl(Some(inquirer), controlMessage)
    }
    case message =>
      logger.info(s"Receiving and ignoring unknown message: ${message.toString}")
  }

  def receiveControl(inquirer: Option[ActorRef], message: Control): Unit = {
    val publish = IO(pubSubMediator ! Publish(eventTopic, message))
    val process = message match {
      case m: UploadSoftwareResult => handleUploadSoftwareResult(m)
      case m: UploadSoftwareRequest => handleUploadSoftwareRequest(inquirer, m)
    }

    (publish *> process).unsafeRunSync()
  }

  def messageForStateAllowed(message: Control, state: HardwareControlState): Boolean = message match {
    case _: UploadSoftwareRequest => state match {
      case Initial => true
      case _ => false
    }
    case _: UploadSoftwareResult => state match {
      case _: Uploading => true
      case _ => false
    }
  }

  def sendToAgent(message: Control): IO[Unit] = IO(out ! message.asJson.noSpaces)
  def sendToRequester(requester: ActorRef, message: Control): IO[Unit] = {
    logger.info(s"Sending upload result to requester ${requester.path.toStringWithoutAddress}")
    IO(requester ! message)
  }

  def handleUploadSoftwareRequest(inquirer: Option[ActorRef], message: UploadSoftwareRequest): IO[Unit] =
    for {
      // Send message to agent or respond with failure immediately
      isUploading <- state match {
        case Initial => sendToAgent(message) *> IO.pure(true)
        case Uploading(Some(requester)) =>
          sendToRequester(requester, UploadSoftwareResult("An upload is already in progress".some)) *> IO.pure(false)
        case Uploading(None) => IO.pure(false)
      }
      // Store the current state of "uploading"
      _ <- if (isUploading) IO { state = Uploading(inquirer) } else IO(())
    } yield ()

  def handleUploadSoftwareResult(message: UploadSoftwareResult): IO[Unit] =
    for {
      // Send message to agent or respond with failure immediately
      isUploaded <- state match {
        case Uploading(Some(requester)) => sendToRequester(requester, message) *> IO.pure(true)
        case Uploading(None) => IO.pure(true)
        case _ => IO.pure(false)
      }
      // Store the current state of "uploading"
      _ <- if (isUploaded) IO { state = Initial } else IO(())
    } yield ()
}

object HardwareControlActor {
  val subscribed = "subscribed"
  def hardwareActor(hardwareId: HardwareId) = f"hardware-${hardwareId.value}-actor"
  def hardwareEventTopic(hardwareId: HardwareId) = f"hardware-${hardwareId.value}-event"
  def props(
    pubSubMediator: ActorRef,
    out: ActorRef,
    hardwareId: HardwareId
  )(implicit
    iort: IORuntime,
    timeout: Timeout
  ): Props = Props(new HardwareControlActor(pubSubMediator, out, hardwareId))

  implicit val transformer: MessageFlowTransformer[Control, String] =
    MessageFlowTransformer.stringMessageFlowTransformer.map(x => {
      decode[Control](x).toTry.getOrElse {
        throw WebSocketCloseException(
          CloseMessage(Some(CloseCodes.Unacceptable), "Failed to parse message"))
      }
    })
}
