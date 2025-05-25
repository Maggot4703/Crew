import javafx.application.Application;
import javafx.scene.Scene;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.layout.VBox;
import javafx.stage.Stage;

public class JavaFXTest extends Application {

    @Override
    public void start(Stage primaryStage) {
        // Create a label
        Label label = new Label("Hello JavaFX on Raspberry Pi 5!");

        // Create a button
        Button button = new Button("Click me!");
        button.setOnAction(e -> label.setText("Button clicked! JavaFX is working!"));

        // Create layout
        VBox root = new VBox(10);
        root.getChildren().addAll(label, button);
        root.setStyle("-fx-padding: 20;");

        // Create scene
        Scene scene = new Scene(root, 300, 200);

        // Set up stage
        primaryStage.setTitle("JavaFX Test on Raspberry Pi 5");
        primaryStage.setScene(scene);
        primaryStage.show();
    }

    public static void main(String[] args) {
        launch(args);
    }
}
