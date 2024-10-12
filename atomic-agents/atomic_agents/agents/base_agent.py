import instructor
from pydantic import BaseModel, Field
from typing import Optional, Type

from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.lib.components.system_prompt_generator import SystemPromptContextProviderBase, SystemPromptGenerator
from atomic_agents.lib.base.base_io_schema import BaseIOSchema


class BaseAgentInputSchema(BaseIOSchema):
    """This schema represents the input from the user to the AI agent."""

    chat_message: str = Field(
        ...,
        description="The chat message sent by the user to the assistant.",
    )


class BaseAgentOutputSchema(BaseIOSchema):
    """This schema represents the response generated by the chat agent."""

    chat_message: str = Field(
        ...,
        description=(
            "The chat message exchanged between the user and the chat agent. "
            "This contains the markdown-enabled response generated by the chat agent."
        ),
    )


class BaseAgentConfig(BaseModel):
    client: instructor.client.Instructor = Field(..., description="Client for interacting with the language model.")
    model: str = Field("gpt-4o-mini", description="The model to use for generating responses.")
    memory: Optional[AgentMemory] = Field(None, description="Memory component for storing chat history.")
    system_prompt_generator: Optional[SystemPromptGenerator] = Field(
        None, description="Component for generating system prompts."
    )
    input_schema: Optional[Type[BaseModel]] = Field(None, description="The schema for the input data.")
    output_schema: Optional[Type[BaseModel]] = Field(None, description="The schema for the output data.")

    model_config = {"arbitrary_types_allowed": True}


class BaseAgent:
    """
    Base class for chat agents.

    This class provides the core functionality for handling chat interactions, including managing memory,
    generating system prompts, and obtaining responses from a language model.

    Attributes:
        input_schema (Type[BaseIOSchema]): Schema for the input data.
        output_schema (Type[BaseIOSchema]): Schema for the output data.
        client: Client for interacting with the language model.
        model (str): The model to use for generating responses.
        memory (AgentMemory): Memory component for storing chat history.
        system_prompt_generator (SystemPromptGenerator): Component for generating system prompts.
        initial_memory (AgentMemory): Initial state of the memory.
    """

    input_schema = BaseAgentInputSchema
    output_schema = BaseAgentOutputSchema

    def __init__(self, config: BaseAgentConfig):
        """
        Initializes the BaseAgent.

        Args:
            config (BaseAgentConfig): Configuration for the chat agent.
        """
        self.input_schema = config.input_schema or self.input_schema
        self.output_schema = config.output_schema or self.output_schema
        self.client = config.client
        self.model = config.model
        self.memory = config.memory or AgentMemory()
        self.system_prompt_generator = config.system_prompt_generator or SystemPromptGenerator()
        self.initial_memory = self.memory.copy()
        self.current_user_input = None

    def reset_memory(self):
        """
        Resets the memory to its initial state.
        """
        self.memory = self.initial_memory.copy()

    def get_response(self, response_model=None) -> Type[BaseModel]:
        """
        Obtains a response from the language model.

        Args:
            response_model (Type[BaseModel], optional):
                The schema for the response data. If not set, self.output_schema is used.

        Returns:
            Type[BaseModel]: The response from the language model.
        """
        if response_model is None:
            response_model = self.output_schema

        messages = [
            {
                "role": "system",
                "content": self.system_prompt_generator.generate_prompt(),
            }
        ] + self.memory.get_history()
        response = self.client.chat.completions.create(model=self.model, messages=messages, response_model=response_model)
        return response

    def run(self, user_input: Optional[Type[BaseIOSchema]] = None) -> Type[BaseIOSchema]:
        """
        Runs the chat agent with the given user input.

        Args:
            user_input (Optional[Type[BaseIOSchema]]): The input from the user. If not provided, skips adding to memory.

        Returns:
            Type[BaseIOSchema]: The response from the chat agent.
        """
        if user_input:
            self.memory.initialize_turn()
            self.current_user_input = user_input
            self.memory.add_message("user", user_input)

        response = self.get_response(response_model=self.output_schema)
        self.memory.add_message("assistant", response)

        return response

    def get_context_provider(self, provider_name: str) -> Type[SystemPromptContextProviderBase]:
        """
        Retrieves a context provider by name.

        Args:
            provider_name (str): The name of the context provider.

        Returns:
            SystemPromptContextProviderBase: The context provider if found.

        Raises:
            KeyError: If the context provider is not found.
        """
        if provider_name not in self.system_prompt_generator.context_providers:
            raise KeyError(f"Context provider '{provider_name}' not found.")
        return self.system_prompt_generator.context_providers[provider_name]

    def register_context_provider(self, provider_name: str, provider: SystemPromptContextProviderBase):
        """
        Registers a new context provider.

        Args:
            provider_name (str): The name of the context provider.
            provider (SystemPromptContextProviderBase): The context provider instance.
        """
        self.system_prompt_generator.context_providers[provider_name] = provider

    def unregister_context_provider(self, provider_name: str):
        """
        Unregisters an existing context provider.

        Args:
            provider_name (str): The name of the context provider to remove.
        """
        if provider_name in self.system_prompt_generator.context_providers:
            del self.system_prompt_generator.context_providers[provider_name]
        else:
            raise KeyError(f"Context provider '{provider_name}' not found.")


if __name__ == "__main__":
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.syntax import Syntax
    from rich import box
    import instructor
    import openai
    from pydantic import BaseModel, Field

    # Initialize the agent
    client = instructor.from_openai(openai.OpenAI())
    config = BaseAgentConfig(
        client=client,
        model="gpt-4o-mini",
    )
    agent = BaseAgent(config)

    # Create a Rich console
    console = Console()

    # Print agent information
    console.print(Panel.fit("[bold blue]Agent Information[/bold blue]", border_style="blue", padding=(1, 1)))

    # Print input schema
    input_schema_table = Table(title="Input Schema", box=box.ROUNDED)
    input_schema_table.add_column("Field", style="cyan")
    input_schema_table.add_column("Type", style="magenta")
    input_schema_table.add_column("Description", style="green")

    for field_name, field in agent.input_schema.model_fields.items():
        input_schema_table.add_row(field_name, str(field.annotation), field.description or "")

    console.print(input_schema_table)

    # Print output schema
    output_schema_table = Table(title="Output Schema", box=box.ROUNDED)
    output_schema_table.add_column("Field", style="cyan")
    output_schema_table.add_column("Type", style="magenta")
    output_schema_table.add_column("Description", style="green")

    for field_name, field in agent.output_schema.model_fields.items():
        output_schema_table.add_row(field_name, str(field.annotation), field.description or "")

    console.print(output_schema_table)

    # Print other agent information
    info_table = Table(title="Agent Configuration", box=box.ROUNDED)
    info_table.add_column("Property", style="cyan")
    info_table.add_column("Value", style="yellow")

    info_table.add_row("Model", agent.model)
    info_table.add_row("Memory", str(type(agent.memory).__name__))
    info_table.add_row("System Prompt Generator", str(type(agent.system_prompt_generator).__name__))

    console.print(info_table)

    # Print a sample of the system prompt
    system_prompt = agent.system_prompt_generator.generate_prompt()
    console.print(
        Panel(
            Syntax(system_prompt, "markdown", theme="monokai", line_numbers=True),
            title="Sample System Prompt",
            border_style="green",
            expand=False,
        )
    )

    console.print("\n[bold]Agent initialized and ready to use![/bold]")

    # Run the agent with a sample input
    sample_input = agent.input_schema(chat_message="Hello, how are you?")
    response = agent.run(sample_input)
    console.print(f"[bold]Response:[/bold] {response.chat_message}")