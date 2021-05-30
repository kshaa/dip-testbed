package iotfrisbee.web.controllers

import scala.annotation.unused
import scala.concurrent.ExecutionContext
import akka.actor.{ActorRef, ActorSystem, Props}
import akka.cluster.pubsub.DistributedPubSubMediator.Publish
import akka.stream.Materializer
import play.api.libs.streams.ActorFlow
import play.api.mvc._
import cats.data.EitherT
import cats.effect.IO
import cats.effect.unsafe.IORuntime
import cats.implicits._
import io.circe.syntax._
import iotfrisbee.database.services.HardwareMessageService
import iotfrisbee.domain.{HardwareId, HardwareMessageId}
import iotfrisbee.protocol._
import iotfrisbee.protocol.Codecs._
import iotfrisbee.protocol.WebResult._
import iotfrisbee.web.actors.HardwareMessageSubscriptionActor
import iotfrisbee.web.actors.HardwareMessageSubscriptionActor.hardwareMessageTopic
import iotfrisbee.web.ioControls.PipelineOps._
import iotfrisbee.web.ioControls._

class HardwareMessageController(
  val cc: ControllerComponents,
  val pubSubMediator: ActorRef,
  val hardwareMessageService: HardwareMessageService[IO],
)(implicit
  @unused ec: ExecutionContext,
  @unused iort: IORuntime,
  @unused actorSystem: ActorSystem,
  @unused materializer: Materializer,
) extends AbstractController(cc)
    with IOController {

  def hardwareMessageSubscription(subscriber: ActorRef, hardwareId: HardwareId): Props =
    HardwareMessageSubscriptionActor.props(pubSubMediator, subscriber, hardwareId)

  def subscribeHardwareMessages(hardwareId: HardwareId): WebSocket =
    WebSocket.accept[String, String](_ => ActorFlow.actorRef(hardwareMessageSubscription(_, hardwareId)))

  def createHardwareMessage: Action[CreateHardwareMessage] =
    IOActionJSON[CreateHardwareMessage](r =>
      for {
        // Create hardware message
        hardwareMessage <- EitherT(
          hardwareMessageService.createHardwareMessage(r.body.messageType, r.body.message, r.body.hardwareId),
        ).leftMap(error => Failure(error.message).withHttpStatus(INTERNAL_SERVER_ERROR))

        // Send out notification about the hardware message
        topic = hardwareMessageTopic(r.body.hardwareId)
        message = hardwareMessage.asJson.toString
        _ <- EitherT[IO, Result, Unit](IO(Right(pubSubMediator ! Publish(topic, message))))

        // Return created hardware message result
        result = Success(hardwareMessage).withHttpStatus(OK)
      } yield result,
    )

  def getHardwareMessages(hardwareId: Option[HardwareId]): Action[AnyContent] =
    IOActionAny { _ =>
      EitherT(hardwareMessageService.getHardwareMessages(hardwareId))
        .bimap(
          error => Failure(error.message).withHttpStatus(INTERNAL_SERVER_ERROR),
          hardwareMessages => Success(hardwareMessages).withHttpStatus(OK),
        )
    }

  def getHardwareMessage(hardwareMessageId: HardwareMessageId): Action[AnyContent] =
    IOActionAny { _ =>
      EitherT(hardwareMessageService.getHardwareMessage(hardwareMessageId))
        .leftMap(error => Failure(error.message).withHttpStatus(INTERNAL_SERVER_ERROR))
        .flatMap(get =>
          EitherT.fromEither(
            get
              .toRight("Hardware message with that id doesn't exist")
              .bimap(
                errorMessage => Failure(errorMessage).withHttpStatus(BAD_REQUEST),
                hardwareMessage => Success(hardwareMessage).withHttpStatus(OK),
              ),
          ),
        )
    }
}
